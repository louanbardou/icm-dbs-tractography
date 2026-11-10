#!/usr/bin/env zsh
# Étape 11 — connectome par arêtes (comme Presidio) : parcellation 388 nœuds en espace natif, matrice SIFT2 du cerveau entier, et pour chaque VTA
# (L, R) matrice des streamlines qui le traversent. Sortie : triangle supérieur (75 078 arêtes) en CSV, une ligne par VTA.
# Usage : SUB=sub-DBS02 T=... L=... zsh scripts/11_edges.sh   (a besoin de 08_tracto/tracks_10M.tck)
set -e; set -o pipefail; export PATH=/Users/louan/opt/ants-2.6.5/bin:$PATH
ICM=${ICM:-/Users/louan/Folder/ICM}; SUB=${SUB:-sub-DBS01}; T=${T:-$ICM/derivatives/tracto}; L=${L:-$ICM/data/bids/derivatives/leaddbs/$SUB}
R=$T/09_rois; TR=$T/08_tracto; O=$T/11_edges; mkdir -p $O
REF=$L/coregistration/anat/${SUB}_ses-preop_space-anchorNative_desc-preproc_acq-iso_T1w.nii
WARP=$L/normalization/transformations/${SUB}_from-MNI152NLin2009bAsym_to-anchorNative_desc-ants.nii.gz
[[ -e $TR/tracks_10M.tck ]] || { echo "manque tracks_10M.tck"; exit 1; }
echo "== parcellation -> natif ($(date +%H:%M:%S))"
antsApplyTransforms -d 3 -i $ICM/data/atlases/parc_mni2009b_1mm.nii.gz -r $REF -n NearestNeighbor -o $O/parc_native_raw.nii.gz -t $WARP
# STN du patient (atlas DISTAL natif des auteurs) = nœuds 387 (L) et 388 (R), écrase la parcellation
mrcalc $R/STN_L.nii.gz 0.5 -gt 387 $O/parc_native_raw.nii.gz -if $O/_p1.mif -force
mrcalc $R/STN_R.nii.gz 0.5 -gt 388 $O/_p1.mif -if $O/parc_native.mif -force
mrconvert $O/parc_native.mif $O/parc_native.nii.gz -datatype uint16 -force; rm -f $O/_p1.mif $O/parc_native.mif $O/parc_native_raw.nii.gz
conn() {  # $1 = tck, $2 = poids, $3 = préfixe de sortie
  tck2connectome $1 $O/parc_native.nii.gz $3_sift2.csv -tck_weights_in $2 -assignment_radial_search 4 -symmetric -zero_diagonal -force
  tck2connectome $1 $O/parc_native.nii.gz $3_count.csv -assignment_radial_search 4 -symmetric -zero_diagonal -force
}
echo "== cerveau entier ($(date +%H:%M:%S))"
conn $TR/tracks_10M.tck $TR/sift2_weights.txt $O/whole
for h in L R; do
  echo "== VTA_$h ($(date +%H:%M:%S))"
  tckedit $TR/tracks_10M.tck $O/vta_$h.tck -include $R/VTA_$h.nii.gz -tck_weights_in $TR/sift2_weights.txt -tck_weights_out $O/vta_${h}_w.txt -force
  conn $O/vta_$h.tck $O/vta_${h}_w.txt $O/vta_$h
  rm -f $O/vta_$h.tck
done
$ICM/tools/.venv/bin/python -I $ICM/scripts/11b_upper_tri.py $O $SUB
echo "== fini $(date +%H:%M:%S)"
