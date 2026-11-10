#!/usr/bin/env zsh
# Étape 7 — segmentation 5 tissus (ACT) sur le T1 anchorNative, par 5ttgen fsl (FSL FAST + FIRST), + interface GM/WM.
# Usage : zsh scripts/07_5tt.sh
set -e; set -o pipefail
ICM=/Users/louan/Folder/ICM
T1=$ICM/derivatives/tracto/05_ref/T1.nii.gz; OUT=$ICM/derivatives/tracto/07_5tt; QC=$ICM/qc/07_5tt
mkdir -p $OUT $QC
echo "== 1. 5ttgen fsl (T1 entier, sans recadrage pour rester sur la grille du T1)"
5ttgen fsl $T1 $OUT/5tt.mif -nocrop -nthreads 10 -scratch $OUT/scratch -nocleanup -force
echo "== 2. interface GM/WM"
5tt2gmwmi $OUT/5tt.mif $OUT/gmwmi.mif -force
echo "== 3. QC"
$ICM/tools/.venv/bin/python $ICM/scripts/qc_5tt.py $OUT $ICM/derivatives/tracto/05_ref $QC $ICM/data/bids/derivatives/leaddbs/sub-DBS01/atlases
echo "== fini. Regarder $QC puis écrire $QC/DECISION.md"
