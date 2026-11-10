#!/usr/bin/env zsh
# Étape 7b — ajoute le STN complet (DISTAL, atlas natif des auteurs) comme substance grise sous-corticale dans le 5TT (FIRST ne segmente pas le STN),
# puis recalcule l'interface GM/WM. Reproduit ce qui avait été fait à la main pour sub-DBS01 (5tt_stn.mif, gmwmi_stn.mif).
set -e; set -o pipefail
ICM=${ICM:-/Users/louan/Folder/ICM}
SUB=${SUB:-sub-DBS01}; T=${T:-$ICM/derivatives/tracto}; QCR=${QCR:-$ICM/qc}; L=${L:-$ICM/data/bids/derivatives/leaddbs/$SUB}
A=$T/07_5tt; export PATH=/Users/louan/opt/ants-2.6.5/bin:$PATH
REF=$T/05_ref/T1.nii.gz; D="$L/atlases/DISTAL Minimal (Ewert 2017)"
for h in lh rh; do antsApplyTransforms -d 3 -i "$D/$h/STN.nii.gz" -r $REF -n Linear -o $A/stn_$h.nii.gz; done
mrcalc $A/stn_lh.nii.gz 0.5 -gt $A/stn_rh.nii.gz 0.5 -gt -add 0 -gt $A/stn_mask_T1grid.nii.gz -datatype uint8 -force
n=$(mrstats $A/stn_mask_T1grid.nii.gz -ignorezero -output count -quiet); echo "STN voxels : $n"
[[ ${n%.*} -gt 100 ]] || { echo "STN vide ou trop petit : arrêt"; exit 4; }
5ttedit -sgm $A/stn_mask_T1grid.nii.gz $A/5tt.mif $A/5tt_stn.mif -force
5tt2gmwmi $A/5tt_stn.mif $A/gmwmi_stn.mif -force
echo "== fini 7b"
