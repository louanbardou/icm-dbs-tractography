#!/bin/bash
# Reprise de /extra/pipeline.sh à partir de l'inférence (le prétraitement est déjà dans /OUTPUTS). Exécuté DANS le conteneur.
export PATH=$PATH:/extra
export FREESURFER_HOME=/extra/freesurfer; source $FREESURFER_HOME/SetUpFreeSurfer.sh
. /extra/fsl/etc/fslconf/fsl.sh; export PATH=$PATH:/extra/fsl/bin; export FSLDIR=/extra/fsl
export ANTSPATH=/extra/ANTS/bin/ants/bin/; export PATH=$PATH:$ANTSPATH:/extra/ANTS/ANTs/Scripts
source /extra/pytorch/bin/activate
rm -f /OUTPUTS/b0_u_lin_atlas_2_5_FOLD_*.nii.gz
NUM_FOLDS=5
for i in $(seq 1 $NUM_FOLDS); do
  echo Performing inference on FOLD: "$i"
  python3.6 /extra/inference.py /OUTPUTS/T1_norm_lin_atlas_2_5.nii.gz /OUTPUTS/b0_d_lin_atlas_2_5.nii.gz /OUTPUTS/b0_u_lin_atlas_2_5_FOLD_"$i".nii.gz /extra/dual_channel_unet/num_fold_"$i"_total_folds_"$NUM_FOLDS"_seed_1_num_epochs_100_lr_0.0001_betas_\(0.9\,\ 0.999\)_weight_decay_1e-05_num_epoch_*.pth || { echo "FOLD $i ECHEC"; exit 1; }
done
echo Taking ensemble average
fslmerge -t /OUTPUTS/b0_u_lin_atlas_2_5_merged.nii.gz /OUTPUTS/b0_u_lin_atlas_2_5_FOLD_*.nii.gz
fslmaths /OUTPUTS/b0_u_lin_atlas_2_5_merged.nii.gz -Tmean /OUTPUTS/b0_u_lin_atlas_2_5.nii.gz
echo Applying inverse xform to undistorted b0
antsApplyTransforms -d 3 -i /OUTPUTS/b0_u_lin_atlas_2_5.nii.gz -r /INPUTS/b0.nii.gz -n BSpline -t [/OUTPUTS/epi_reg_d_ANTS.txt,1] -t [/OUTPUTS/ANTS0GenericAffine.mat,1] -o /OUTPUTS/b0_u.nii.gz
fslmaths /INPUTS/b0.nii.gz -s 1.15 /OUTPUTS/b0_d_smooth.nii.gz
echo Running topup
fslmerge -t /OUTPUTS/b0_all.nii.gz /OUTPUTS/b0_d_smooth.nii.gz /OUTPUTS/b0_u.nii.gz
topup -v --imain=/OUTPUTS/b0_all.nii.gz --datain=/INPUTS/acqparams.txt --config=/extra/synb0.cnf --iout=/OUTPUTS/b0_all_topup.nii.gz --out=/OUTPUTS/topup
echo FINISHED!!!
