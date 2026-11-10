#!/usr/bin/env zsh
# Étape 7 — segmentation 5 tissus (ACT) sur le T1 anchorNative, par 5ttgen fsl (FSL FAST + FIRST), + interface GM/WM.
# Usage : zsh scripts/07_5tt.sh
set -e; set -o pipefail
ICM=${ICM:-${0:A:h:h}}
SUB=${SUB:-sub-DBS01}; T=${T:-$ICM/derivatives/tracto}; QCR=${QCR:-$ICM/qc}; L=${L:-$ICM/data/bids/derivatives/leaddbs/$SUB}
T1=$T/05_ref/T1.nii.gz; OUT=$T/07_5tt; QC=$QCR/07_5tt
mkdir -p $OUT $QC
echo "== 1. 5ttgen fsl (T1 entier, sans recadrage pour rester sur la grille du T1)"
5ttgen fsl $T1 $OUT/5tt.mif -nocrop -nthreads 10 -scratch $OUT/scratch -nocleanup -force
echo "== 2. interface GM/WM"
5tt2gmwmi $OUT/5tt.mif $OUT/gmwmi.mif -force
echo "== 3. QC"
${PYTHON:-python3} $ICM/scripts/qc_5tt.py $OUT $T/05_ref $QC $L/atlases
echo "== fini. Regarder $QC puis écrire $QC/DECISION.md"
