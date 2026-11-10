#!/usr/bin/env zsh
# Étape 5 — recalage rigide DWI -> T1 anchorNative (Lead-DBS), pour une variante (03a_eddy ou 03b_eddy). Header seulement, pas de rééchantillonnage de la DWI.
# Usage : zsh scripts/05_coreg.sh 03a_eddy ; zsh scripts/05_coreg.sh 03b_eddy
set -e; set -o pipefail
V=$1; [[ -z $V ]] && { echo "usage: $0 03a_eddy|03b_eddy"; exit 1; }
ICM=${ICM:-/Users/louan/Folder/ICM}
SUB=${SUB:-sub-DBS01}; T=${T:-$ICM/derivatives/tracto}; QCR=${QCR:-$ICM/qc}; L=${L:-$ICM/data/bids/derivatives/leaddbs/$SUB}
T1=$L/coregistration/anat/${SUB}_ses-preop_space-anchorNative_desc-preproc_acq-iso_T1w.nii
REF=$T/05_ref; I=$T/04_${V}; OUT=$T/05_${V}; QC=$QCR/05_${V}
mkdir -p $REF $OUT $QC
if [[ ! -f $REF/T1_brain_mask.nii.gz ]]; then
  echo "== T1 : extraction du cerveau (bet) — commun aux deux variantes"
  cp $T1 $REF/T1.nii; gzip -f $REF/T1.nii
  bet $REF/T1.nii.gz $REF/T1_brain -m -R -f 0.4
fi
echo "== [$V] b0 masqué"
fslmaths $I/b0.nii.gz -mas $I/mask.nii.gz $OUT/b0_brain
echo "== [$V] flirt rigide 6 ddl, information mutuelle (b0 -> T1 cerveau)"
flirt -in $OUT/b0_brain -ref $REF/T1_brain -dof 6 -cost mutualinfo -searchrx -30 30 -searchry -30 30 -searchrz -30 30 \
  -omat $OUT/b02t1.mat -out $OUT/b0_in_T1 -interp spline
echo "== [$V] conversion pour MRtrix et application à l'en-tête de la DWI et du masque"
transformconvert $OUT/b02t1.mat $OUT/b0_brain.nii.gz $REF/T1.nii.gz flirt_import $OUT/dwi2T1.txt -force
mrtransform $I/dwi_unb.mif -linear $OUT/dwi2T1.txt $OUT/dwi_T1.mif -force
mrtransform $I/mask.mif -linear $OUT/dwi2T1.txt $OUT/mask_T1.mif -force
mrtransform $I/mask.mif -linear $OUT/dwi2T1.txt -template $REF/T1.nii.gz -interp nearest $OUT/mask_in_T1grid.nii.gz -force
echo "== [$V] QC"
$ICM/tools/.venv/bin/python $ICM/scripts/qc_coreg.py $REF $OUT $QC $L/atlases
echo "== fini [$V]. Regarder $QC puis écrire $QC/DECISION.md"
