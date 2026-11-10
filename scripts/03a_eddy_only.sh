#!/usr/bin/env zsh
# Étape 3, option A — mouvement + courants de Foucault avec FSL eddy, SANS correction de susceptibilité (pas de reverse-PE).
# Usage : zsh scripts/03a_eddy_only.sh        (30-60 min sur M1 Max)
set -e
ICM=/Users/louan/Folder/ICM
IN=$ICM/derivatives/tracto/02_denoise/dwi_den_unr.mif
OUT=$ICM/derivatives/tracto/03a_eddy
QC=$ICM/qc/03a_eddy
SCRATCH=$OUT/scratch
mkdir -p $OUT $QC
rm -rf $SCRATCH

echo "== 1. dwifslpreproc (prépare acqparams/index, lance eddy_cpu, réapplique les bvec tournés)"
dwifslpreproc $IN $OUT/dwi_preproc.mif \
  -rpe_none -pe_dir j -readout_time 0.0202278 \
  -eddy_options " --slm=linear --repol --data_is_shelled --niter=8 --fwhm=10,8,4,2,0,0,0,0" \
  -eddyqc_all $QC/eddy_outputs \
  -scratch $SCRATCH -nocleanup -nthreads 10 -force

echo "== 2. eddy_quad : rapport QC (mouvement, outliers, SNR/CNR)"
cd $SCRATCH
eddy_quad dwi_post_eddy -idx eddy_indices.txt -par eddy_config.txt -m eddy_mask.nii -b bvals -o $QC/eddy_quad || echo "eddy_quad a échoué (non bloquant)"
cd $ICM

echo "== 3. b0 et moyennes avant/après pour la visu"
dwiextract $OUT/dwi_preproc.mif -bzero - | mrmath - mean $OUT/b0_preproc.mif -axis 3 -force
dwiextract $OUT/dwi_preproc.mif -shells 1000 - | mrmath - mean $OUT/mean_b1000_preproc.mif -axis 3 -force

echo "== 4. montages QC"
$ICM/tools/.venv/bin/python $ICM/scripts/qc_eddy_montage.py $IN $OUT/dwi_preproc.mif $SCRATCH $QC
echo "== fini. Regarder $QC puis écrire $QC/DECISION.md"
