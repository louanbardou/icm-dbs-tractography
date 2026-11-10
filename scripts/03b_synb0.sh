#!/usr/bin/env zsh
# Étape 3, option B, partie 1 — Synb0-DISCO : b0 synthétique non distordu depuis le T1, puis topup (dans le conteneur).
# Usage : zsh scripts/03b_synb0.sh        (Docker Desktop doit tourner ; ~1-2 h la première fois, FreeSurfer inclus)
set -e
ICM=/Users/louan/Folder/ICM
IN=$ICM/derivatives/tracto/02_denoise/dwi_den_unr.mif
T1=$ICM/data/bids/derivatives/leaddbs/sub-DBS01/coregistration/anat/sub-DBS01_ses-preop_space-anchorNative_desc-preproc_acq-iso_T1w.nii
OUT=$ICM/derivatives/tracto/03b_synb0
mkdir -p $OUT/INPUTS $OUT/OUTPUTS

echo "== 1. entrées : b0 débruité (distordu) + T1 + acqparams"
dwiextract $IN -bzero - | mrmath - mean - -axis 3 | mrconvert - $OUT/INPUTS/b0.nii.gz -force
mrconvert $T1 $OUT/INPUTS/T1.nii.gz -force
printf '0 1 0 0.0202278\n0 1 0 0.000\n' > $OUT/INPUTS/acqparams.txt

echo "== 2. synb0-disco (conteneur linux/amd64 émulé sur M1, lent)"
docker run --rm --platform linux/amd64 \
  -v $OUT/INPUTS:/INPUTS -v $OUT/OUTPUTS:/OUTPUTS \
  -v $HOME/.freesurfer/license.txt:/extra/freesurfer/license.txt \
  --user $(id -u):$(id -g) \
  leonyichencai/synb0-disco:v3.1 2>&1 | tee $OUT/synb0.log
echo "== fini. Sorties dans $OUT/OUTPUTS (b0_u.nii.gz = b0 synthétique, b0_all_topup.nii.gz)"
