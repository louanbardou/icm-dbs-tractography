#!/bin/bash
# Étape 9a+9b (cohorte) — ROI corticaux/sous-corticaux en espace natif anchorNative d'un patient. Usage : SUB=sub-DBS02 T=... bash scripts/09_rois_cohort.sh
set -e
[[ -n $ANTS_BIN ]] && export PATH=$ANTS_BIN:$PATH
ICM=${ICM:-$(cd "$(dirname "$0")/.." && pwd)}; SUB=${SUB:?SUB}; T=${T:?T}; L=${L:-$ICM/data/bids/derivatives/leaddbs/$SUB}
O=$T/09_rois; mkdir -p $O; G=$ICM/derivatives/cohort/_shared/fsl2009b; mkdir -p $G
A=$FSLDIR/data/atlases
TPL=${LEADDBS_DIR:-$HOME/opt/leaddbs}/templates/space/MNI152NLin2009bAsym/t1.nii
REF=$L/coregistration/anat/${SUB}_ses-preop_space-anchorNative_desc-preproc_acq-iso_T1w.nii
WARP=$L/normalization/transformations/${SUB}_from-MNI152NLin2009bAsym_to-anchorNative_desc-ants.nii.gz
if [ ! -f $G/fsl2009b_1Warp.nii.gz ]; then
  ResampleImageBySpacing 3 $TPL $G/t1_mni2009b_1mm.nii.gz 1 1 1 0 0 1
  antsRegistrationSyN.sh -d 3 -f $G/t1_mni2009b_1mm.nii.gz -m $FSLDIR/data/standard/MNI152_T1_1mm.nii.gz -o $G/fsl2009b_ -t s -n 8
fi
for atl in Juelich/Juelich-maxprob-thr25-1mm HarvardOxford/HarvardOxford-cort-maxprob-thr25-1mm HarvardOxford/HarvardOxford-sub-maxprob-thr25-1mm; do
  b=$(basename $atl)
  antsApplyTransforms -d 3 -i $A/$atl.nii.gz -r $REF -n NearestNeighbor -o $O/${b}_native.nii.gz -t $WARP -t $G/fsl2009b_1Warp.nii.gz -t $G/fsl2009b_0GenericAffine.mat
done
SUB=$SUB T=$T L=$L ${PYTHON:-python3} $ICM/scripts/09b_rois_masks.py
