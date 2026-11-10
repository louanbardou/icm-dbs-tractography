#!/usr/bin/env zsh
# Étape 3, option B, partie 1 — Synb0-DISCO : b0 synthétique non distordu depuis le T1, puis topup (dans le conteneur).
# Usage : zsh scripts/03b_synb0.sh        (Docker Desktop doit tourner ; ~1-2 h la première fois, FreeSurfer inclus)
set -e
ICM=${ICM:-${0:A:h:h}}
SUB=${SUB:-sub-DBS01}; T=${T:-$ICM/derivatives/tracto}; QCR=${QCR:-$ICM/qc}; L=${L:-$ICM/data/bids/derivatives/leaddbs/$SUB}
IN=$T/02_denoise/dwi_den_unr.mif
T1=$L/coregistration/anat/${SUB}_ses-preop_space-anchorNative_desc-preproc_acq-iso_T1w.nii
OUT=$T/03b_synb0
mkdir -p $OUT/INPUTS $OUT/OUTPUTS

echo "== 1. entrées : b0 débruité (distordu) + T1 + acqparams"
dwiextract $IN -bzero - | mrmath - mean - -axis 3 | mrconvert - $OUT/INPUTS/b0.nii.gz -force
mrconvert $T1 $OUT/INPUTS/T1.nii.gz -force
J=${DWIJSON:-$ICM/data/bids/${SUB}/ses-preop/dwi/${SUB}_ses-preop_dwi.json}
TRT=$(python3 -c "import json,sys;print(json.load(open('$J'))['TotalReadoutTime'])"); PE=$(python3 -c "import json;print(json.load(open('$J'))['PhaseEncodingDirection'])")
[[ $PE == j ]] || { echo "PE=$PE non géré (attendu j)"; exit 3; }
printf "0 1 0 $TRT\n0 1 0 0.000\n" > $OUT/INPUTS/acqparams.txt

echo "== 2. synb0-disco (conteneur linux/amd64 émulé sur M1, lent)"
if command -v docker >/dev/null 2>&1; then
  docker run --rm --platform linux/amd64 \
    -v $OUT/INPUTS:/INPUTS -v $OUT/OUTPUTS:/OUTPUTS \
    -v $HOME/.freesurfer/license.txt:/extra/freesurfer/license.txt \
    --user $(id -u):$(id -g) \
    leonyichencai/synb0-disco:v3.1 2>&1 | tee $OUT/synb0.log
else   # serveur : on EST dans le conteneur synb0-disco ; /INPUTS et /OUTPUTS sont globaux, donc un seul patient à la fois (verrou)
  sed "s#/INPUTS#$OUT/INPUTS#g; s#/OUTPUTS#$OUT/OUTPUTS#g" /extra/pipeline.sh > $OUT/pipeline_local.sh   # chemins du patient : plusieurs patients en parallèle
  bash $OUT/pipeline_local.sh 2>&1 | tee $OUT/synb0.log; [[ ${pipestatus[1]} -eq 0 ]] || exit 1
fi
[[ -e $OUT/OUTPUTS/b0_all_topup.nii.gz ]] || { echo "ÉCHEC : b0_all_topup.nii.gz absent"; exit 1; }
echo "== fini. Sorties dans $OUT/OUTPUTS (b0_u.nii.gz = b0 synthétique, b0_all_topup.nii.gz)"
