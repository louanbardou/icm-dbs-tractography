#!/usr/bin/env zsh
# Étape 4 — correction de biais + masque cérébral, pour une variante de l'étape 3 (03a_eddy ou 03b_eddy).
# Usage : zsh scripts/04_bias_mask.sh 03a_eddy      puis      zsh scripts/04_bias_mask.sh 03b_eddy
set -e; set -o pipefail
V=$1; [[ -z $V ]] && { echo "usage: $0 03a_eddy|03b_eddy"; exit 1; }
ICM=${ICM:-${0:A:h:h}}
SUB=${SUB:-sub-DBS01}; T=${T:-$ICM/derivatives/tracto}; QCR=${QCR:-$ICM/qc}; L=${L:-$ICM/data/bids/derivatives/leaddbs/$SUB}
IN=$T/$V/dwi_preproc.mif
OUT=$T/04_${V}; QC=$QCR/04_${V}
mkdir -p $OUT $QC
echo "== [$V] biais (ANTs N4)"
dwibiascorrect ants $IN $OUT/dwi_unb.mif -bias $OUT/bias.mif -nthreads 10 -force
echo "== [$V] masque dwi2mask + bet sur le b0 (comparaison)"
dwi2mask $OUT/dwi_unb.mif $OUT/mask.mif -force
dwiextract $OUT/dwi_unb.mif -bzero - | mrmath - mean $OUT/b0.mif -axis 3 -force
mrconvert $OUT/b0.mif $OUT/b0.nii.gz -force
mrconvert $OUT/mask.mif $OUT/mask.nii.gz -force
bet $OUT/b0.nii.gz $OUT/b0_bet -m -f 0.3 -R
echo "== [$V] QC"
${PYTHON:-python3} $ICM/scripts/qc_mask.py $OUT $QC
echo "== fini [$V]. Regarder $QC puis écrire $QC/DECISION.md"
