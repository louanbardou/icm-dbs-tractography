#!/bin/bash
# Étape 9a : ROI corticales (M1, BA6, SMA) en espace natif anchorNative.
# Chaîne : atlas FSL (MNI152NLin6Asym) -> [ANTs affine+SyN] -> T1 patient normalisé (NLin2009bAsym)
#          -> [warp Lead-DBS] -> anchorNative (grille T1 0,7 mm).
set -e
export PATH=/Users/louan/opt/ants-2.6.5/bin:$PATH
R=/Users/louan/Folder/ICM; L=$R/data/bids/derivatives/leaddbs/sub-DBS01
O=$R/derivatives/tracto/09_rois; cd $O
A=$FSLDIR/data/atlases
T2009=$L/normalization/anat/sub-DBS01_ses-preop_space-MNI152NLin2009bAsym_desc-preproc_acq-iso_T1w.nii
REF=$L/coregistration/anat/sub-DBS01_ses-preop_space-anchorNative_desc-preproc_acq-iso_T1w.nii
WARP=$L/normalization/transformations/sub-DBS01_from-MNI152NLin2009bAsym_to-anchorNative_desc-ants.nii.gz
echo "== 1. T1 patient (MNI2009b) -> 1 mm"
[ -f t1_mni2009b_1mm.nii.gz ] || ResampleImageBySpacing 3 $T2009 t1_mni2009b_1mm.nii.gz 1 1 1 0 0 1
echo "== 2. FSL MNI -> MNI2009b"
[ -f fsl2009b_1Warp.nii.gz ] || antsRegistrationSyN.sh -d 3 -f t1_mni2009b_1mm.nii.gz -m $FSLDIR/data/standard/MNI152_T1_1mm.nii.gz -o fsl2009b_ -t s -n 8
echo "== 3. labels -> natif"
for atl in Juelich/Juelich-maxprob-thr25-1mm HarvardOxford/HarvardOxford-cort-maxprob-thr25-1mm; do
  b=$(basename $atl)
  antsApplyTransforms -d 3 -i $A/$atl.nii.gz -r $REF -n NearestNeighbor -o ${b}_native.nii.gz \
    -t $WARP -t fsl2009b_1Warp.nii.gz -t fsl2009b_0GenericAffine.mat
done
echo "== fini"
