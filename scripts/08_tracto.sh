#!/usr/bin/env zsh
# Étape 8 — tractographie globale iFOD2 + ACT (5tt avec STN en GM sous-corticale), seeds à l'interface GM/WM, puis SIFT2.
# Usage : zsh scripts/08_tracto.sh        (45-90 min estimés sur M1 Max ; tout est local)
set -e; set -o pipefail
ICM=${ICM:-/Users/louan/Folder/ICM}
SUB=${SUB:-sub-DBS01}; T=${T:-$ICM/derivatives/tracto}; QCR=${QCR:-$ICM/qc}; L=${L:-$ICM/data/bids/derivatives/leaddbs/$SUB}
F=$T/06_fod; A=$T/07_5tt; OUT=$T/08_tracto; QC=$QCR/08_tracto
mkdir -p $OUT $QC
echo "== 1. tckgen 10M (iFOD2, ACT, backtrack, crop_at_gmwmi, seed_gmwmi) — début $(date +%H:%M:%S)"
tckgen $F/wmfod_norm.mif $OUT/tracks_10M.tck -act $A/5tt_stn.mif -backtrack -crop_at_gmwmi -seed_gmwmi $A/gmwmi_stn.mif \
  -select 10M -algorithm iFOD2 -nthreads ${NTHR:-10} -force
echo "== 2. tcksift2 — début $(date +%H:%M:%S)"
tcksift2 $OUT/tracks_10M.tck $F/wmfod_norm.mif $OUT/sift2_weights.txt -act $A/5tt_stn.mif -out_mu $OUT/sift2_mu.txt -nthreads ${NTHR:-10} -force
echo "== 3. sous-échantillon pour la visu + TDI (pondérée SIFT2)"
tckedit $OUT/tracks_10M.tck -number 200k $OUT/tracks_200k.tck -force
tckmap $OUT/tracks_10M.tck -tck_weights_in $OUT/sift2_weights.txt -template $T/05_ref/T1.nii.gz -vox 1 $OUT/tdi_sift2_1mm.mif -force
tckstats $OUT/tracks_10M.tck -output mean -output median -output count > $OUT/stats.txt 2>&1 || true
echo "== 4. QC — début $(date +%H:%M:%S)"
$ICM/tools/.venv/bin/python $ICM/scripts/qc_tracto.py $OUT $T/05_ref $A $QC
echo "== fini $(date +%H:%M:%S). Regarder $QC puis écrire $QC/DECISION.md"
