#!/usr/bin/env zsh
# Étape 3, option B, partie 2 — eddy avec le champ topup issu de Synb0-DISCO (dwifslpreproc ne sait pas réutiliser un topup existant : on appelle eddy_cpu directement).
# Usage : zsh scripts/03b_eddy_topup.sh        (30-60 min sur M1 Max)
set -e
set -o pipefail
ICM=/Users/louan/Folder/ICM
IN=$ICM/derivatives/tracto/02_denoise/dwi_den_unr.mif
SYN=$ICM/derivatives/tracto/03b_synb0
OUT=$ICM/derivatives/tracto/03b_eddy
QC=$ICM/qc/03b_eddy
S=$OUT/scratch
mkdir -p $OUT $QC; rm -rf $S; mkdir -p $S

echo "== 1. export NIfTI + bvals/bvecs, index (tous les volumes = ligne 1 de acqparams), masque issu du b0 corrigé"
mrconvert $IN $S/dwi.nii.gz -export_grad_fsl $S/bvecs $S/bvals -force
cp $S/bvals $S/bvals.orig
nvol=$(wc -w < $S/bvals); for i in $(seq 1 $nvol); do printf '1 '; done > $S/index.txt
head -1 $SYN/INPUTS/acqparams.txt > $S/acqp.txt     # eddy refuse un readout nul : on ne garde que la ligne du vrai b0 (la ligne 2 = b0 synthétique ne sert qu'à topup)
fslmaths $SYN/OUTPUTS/b0_all_topup.nii.gz -Tmean $S/b0_topup_mean
bet $S/b0_topup_mean $S/b0_brain -m -f 0.2 -R
cp $SYN/OUTPUTS/topup_fieldcoef.nii.gz $SYN/OUTPUTS/topup_movpar.txt $S/

echo "== 2. eddy_cpu avec --topup"
eddy_cpu --imain=$S/dwi.nii.gz --mask=$S/b0_brain_mask.nii.gz --acqp=$S/acqp.txt --index=$S/index.txt \
  --bvecs=$S/bvecs --bvals=$S/bvals --topup=$S/topup --out=$S/dwi_post_eddy \
  --slm=linear --repol --data_is_shelled --niter=8 --fwhm=10,8,4,2,0,0,0,0 --nthr=10 -v 2>&1 | tee $QC/eddy.log

echo "== 3. retour en .mif avec les bvec tournés"
mrconvert $S/dwi_post_eddy.nii.gz $OUT/dwi_preproc.mif -fslgrad $S/dwi_post_eddy.eddy_rotated_bvecs $S/bvals -force
dwiextract $OUT/dwi_preproc.mif -bzero - | mrmath - mean $OUT/b0_preproc.mif -axis 3 -force
dwiextract $OUT/dwi_preproc.mif -shells 1000 - | mrmath - mean $OUT/mean_b1000_preproc.mif -axis 3 -force

echo "== 4. eddy_quad + montages QC"
eddy_quad $S/dwi_post_eddy -idx $S/index.txt -par $S/acqp.txt -m $S/b0_brain_mask.nii.gz -b $S/bvals -o $QC/eddy_quad || echo "eddy_quad a échoué (non bloquant)"
$ICM/tools/.venv/bin/python $ICM/scripts/qc_eddy_montage.py $IN $OUT/dwi_preproc.mif $S $QC
echo "== fini. Regarder $QC puis écrire $QC/DECISION.md"
