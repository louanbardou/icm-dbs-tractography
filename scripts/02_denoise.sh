#!/usr/bin/env zsh
# Étape 2 — débruitage MP-PCA (dwidenoise) + suppression des anneaux de Gibbs (mrdegibbs). Usage : zsh scripts/02_denoise.sh
set -e
ICM=${ICM:-${0:A:h:h}}
SUB=${SUB:-sub-DBS01}; T=${T:-$ICM/derivatives/tracto}; QCR=${QCR:-$ICM/qc}; L=${L:-$ICM/data/bids/derivatives/leaddbs/$SUB}
IN=$T/01_raw/dwi.mif
OUT=$T/02_denoise
QC=$QCR/02_denoise
mkdir -p $OUT $QC

echo "== 1. dwidenoise : MP-PCA, fenêtre 5x5x5 (défaut), sort aussi la carte de bruit sigma"
dwidenoise $IN $OUT/dwi_den.mif -noise $OUT/noise_sigma.mif -nthreads 10 -force

echo "== 2. résidu = brut - débruité (doit être du bruit pur, sans anatomie)"
mrcalc $IN $OUT/dwi_den.mif -subtract $OUT/residual.mif -force

echo "== 3. mrdegibbs : anneaux de Gibbs, dans le plan de coupe (axes 0,1 = x,y)"
mrdegibbs $OUT/dwi_den.mif $OUT/dwi_den_unr.mif -axes 0,1 -nthreads 10 -force

echo "== 4. montages QC"
${PYTHON:-python3} $ICM/scripts/qc_denoise_montage.py $IN $OUT/dwi_den.mif $OUT/dwi_den_unr.mif $OUT/residual.mif $OUT/noise_sigma.mif $QC
echo "== fini. Regarder $QC puis écrire $QC/DECISION.md"
