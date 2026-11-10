#!/usr/bin/env zsh
# Étape 5a — T1 anchorNative de référence + extraction du cerveau (partie de 05_coreg.sh, séparée pour pouvoir lancer 5TT/ROI avant la DWI).
set -e; set -o pipefail
ICM=${ICM:-/Users/louan/Folder/ICM}
SUB=${SUB:-sub-DBS01}; T=${T:-$ICM/derivatives/tracto}; L=${L:-$ICM/data/bids/derivatives/leaddbs/$SUB}
REF=$T/05_ref; mkdir -p $REF
T1=$L/coregistration/anat/${SUB}_ses-preop_space-anchorNative_desc-preproc_acq-iso_T1w.nii
cp $T1 $REF/T1.nii; gzip -f $REF/T1.nii
bet $REF/T1.nii.gz $REF/T1_brain -m -R -f 0.4
