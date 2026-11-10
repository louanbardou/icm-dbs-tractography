#!/usr/bin/env zsh
# Étape 6 — fonctions de réponse (Dhollander) + FOD multi-shell multi-tissu (MSMT-CSD) + normalisation d'intensité. Variante retenue : 03b_eddy.
# Usage : zsh scripts/06_fod.sh
set -e; set -o pipefail
V=03b_eddy
ICM=${ICM:-${0:A:h:h}}
SUB=${SUB:-sub-DBS01}; T=${T:-$ICM/derivatives/tracto}; QCR=${QCR:-$ICM/qc}; L=${L:-$ICM/data/bids/derivatives/leaddbs/$SUB}
I=$T/05_${V}; OUT=$T/06_fod; QC=$QCR/06_fod
mkdir -p $OUT $QC
echo "== 1. fonctions de réponse WM/GM/CSF (dhollander, sans a priori)"
dwi2response dhollander $I/dwi_T1.mif $OUT/wm.txt $OUT/gm.txt $OUT/csf.txt -voxels $OUT/voxels.mif -mask $I/mask_T1.mif -nthreads 10 -force
echo "== 2. MSMT-CSD"
dwi2fod msmt_csd $I/dwi_T1.mif $OUT/wm.txt $OUT/wmfod.mif $OUT/gm.txt $OUT/gm.mif $OUT/csf.txt $OUT/csf.mif -mask $I/mask_T1.mif -nthreads 10 -force
echo "== 3. mtnormalise (corrige le biais résiduel et normalise les 3 tissus entre eux)"
mtnormalise $OUT/wmfod.mif $OUT/wmfod_norm.mif $OUT/gm.mif $OUT/gm_norm.mif $OUT/csf.mif $OUT/csf_norm.mif -mask $I/mask_T1.mif -nthreads 10 -force
echo "== 4. pics de FOD pour la visu"
sh2peaks $OUT/wmfod_norm.mif $OUT/peaks.mif -num 3 -threshold 0.1 -mask $I/mask_T1.mif -force
echo "== 5. QC"
${PYTHON:-python3} $ICM/scripts/qc_fod.py $OUT $I $QC
echo "== fini. Regarder $QC puis écrire $QC/DECISION.md"
