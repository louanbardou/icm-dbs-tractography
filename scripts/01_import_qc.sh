#!/usr/bin/env zsh
# Étape 1 — import DWI dans MRtrix3 + QC brut. Usage : zsh scripts/01_import_qc.sh
set -e
ICM=${ICM:-${0:A:h:h}}
SUB=${SUB:-sub-DBS01}; T=${T:-$ICM/derivatives/tracto}; QCR=${QCR:-$ICM/qc}; L=${L:-$ICM/data/bids/derivatives/leaddbs/$SUB}
DWI=$ICM/data/bids/${SUB}/ses-preop/dwi/${SUB}_ses-preop_dwi
OUT=$T/01_raw
QC=$QCR/01_raw
mkdir -p $OUT $QC

echo "== 1. import nii + bvec/bval + json -> mif"
mrconvert $DWI.nii.gz -fslgrad $DWI.bvec $DWI.bval -json_import $DWI.json $OUT/dwi.mif -force

echo "== 2. shells"
mrinfo $OUT/dwi.mif -shell_bvalues -shell_sizes

echo "== 3. b0 moyen, et moyenne par shell (pour la visu)"
dwiextract $OUT/dwi.mif -bzero - | mrmath - mean $OUT/b0.mif -axis 3 -force
dwiextract $OUT/dwi.mif -shells 1000 - | mrmath - mean $OUT/mean_b1000.mif -axis 3 -force
dwiextract $OUT/dwi.mif -shells 2000 - | mrmath - mean $OUT/mean_b2000.mif -axis 3 -force

echo "== 4. masque grossier pour le QC (pas le masque final)"
dwi2mask $OUT/dwi.mif $OUT/mask_rough.mif -force

echo "== 5. vérification du sens des bvec (dwigradcheck, ~1-2 min)"
dwigradcheck $OUT/dwi.mif -mask $OUT/mask_rough.mif -number 10000 -force 2>&1 | tee $QC/dwigradcheck_full.txt | grep -A8 'Mean length' | tee $QC/dwigradcheck.txt

echo "== 6. montages PNG"
${PYTHON:-python3} $ICM/scripts/qc_dwi_montage.py $OUT/dwi.mif $QC

echo "== fini. Regarder $QC puis écrire $QC/DECISION.md (GO / NO-GO)"
