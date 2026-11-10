#!/usr/bin/env zsh
# Pipeline complet pour UN patient, sans intervention : DWI -> tractographie -> ROI -> faisceaux DBS. Reprise possible (étapes déjà faites sautées).
# Usage : zsh scripts/run_subject.sh sub-DBS02
# Sorties : derivatives/cohort/<SUB>/ (intermédiaires supprimés à la fin), qc_cohort/<SUB>/, derivatives/cohort/<SUB>/summary.tsv
set -o pipefail
export SUB=$1; [[ -z $SUB ]] && { echo "usage: $0 sub-DBSxx"; exit 1; }
export ICM=/Users/louan/Folder/ICM; export T=$ICM/derivatives/cohort/$SUB; export QCR=$ICM/qc_cohort/$SUB
export L=$ICM/data/bids/derivatives/leaddbs/$SUB
[[ -e $T/DONE ]] && { echo "[$SUB] déjà terminé"; exit 0; }
S=$ICM/scripts; LOG=$T/log; mkdir -p $T $QCR $LOG
export PATH=/Users/louan/opt/ants-2.6.5/bin:$PATH
step(){ # nom, fichier témoin, commande...
  n=$1; sentinel=$2; shift 2
  if [[ -e $T/$sentinel ]]; then echo "[$SUB] $n : déjà fait"; return 0; fi
  echo "[$SUB] $n : début $(date +%H:%M:%S)"
  if ! "$@" > $LOG/$n.log 2>&1; then echo "[$SUB] $n : ÉCHEC (voir $LOG/$n.log)"; echo "$n" > $T/FAILED; return 1; fi
}
# prérequis
for f in $ICM/data/bids/$SUB/ses-preop/dwi/${SUB}_ses-preop_dwi.nii.gz $L/coregistration/anat/${SUB}_ses-preop_space-anchorNative_desc-preproc_acq-iso_T1w.nii \
         $L/normalization/transformations/${SUB}_from-MNI152NLin2009bAsym_to-anchorNative_desc-ants.nii.gz $L/prefs; do
  [[ -e $f ]] || { echo "[$SUB] manque $f"; exit 2; }; done
rm -f $T/FAILED
step 01_import      01_raw/dwi.mif                     zsh $S/01_import_qc.sh   || exit 1
# contrôle automatique des bvec : le meilleur essai doit être l'identité (aucun flip, permutation 0,1,2) et nettement supérieur aux autres
$ICM/tools/.venv/bin/python - <<PY || { echo "[$SUB] bvec : contrôle dwigradcheck NON concluant (voir $QCR/01_raw/dwigradcheck.txt)"; echo bvec > $T/FAILED; exit 1; }
import re,sys
L=[l.split() for l in open("$QCR/01_raw/dwigradcheck.txt") if re.match(r'^\s*[0-9.]+\s',l)]
if not L: sys.exit(1)
best=L[0]; ident=lambda r: r[1]=='none' and ''.join(r[2:5])=='(0,1,2)'
others=[float(r[0]) for r in L if not ident(r)]
ok=ident(best) and others and float(best[0])/max(others)>1.3
print('bvec ok' if ok else 'bvec NON ok', best, max(others) if others else None); sys.exit(0 if ok else 1)
PY
step 02_denoise     02_denoise/dwi_den_unr.mif         zsh $S/02_denoise.sh     || exit 1
step 05a_ref        05_ref/T1_brain_mask.nii.gz         zsh $S/05a_ref.sh        || exit 1
step 07_5tt         07_5tt/5tt.mif                     zsh $S/07_5tt.sh         || exit 1
step 07b_stn        07_5tt/5tt_stn.mif                 zsh $S/07b_stn.sh        || exit 1
step 09_rois        09_rois/cortexmotor_R.nii.gz       bash $S/09_rois_cohort.sh || exit 1
waitdocker(){ until docker info >/dev/null 2>&1; do echo "[$SUB] Docker arrêté : en attente ($(date +%H:%M))"; open -g -b com.docker.docker 2>/dev/null; sleep 120; done; }
[[ -e $T/03b_synb0/OUTPUTS/b0_all_topup.nii.gz ]] || ! command -v docker >/dev/null || waitdocker
step 03b_synb0      03b_synb0/OUTPUTS/b0_all_topup.nii.gz zsh $S/03b_synb0.sh   || exit 1
step 03b_eddy       03b_eddy/dwi_preproc.mif           zsh $S/03b_eddy_topup.sh || exit 1
step 04_bias_mask   04_03b_eddy/mask.mif               zsh $S/04_bias_mask.sh 03b_eddy || exit 1
step 05_coreg       05_03b_eddy/dwi_T1.mif             zsh $S/05_coreg.sh 03b_eddy || exit 1
step 06_fod         06_fod/wmfod_norm.mif              zsh $S/06_fod.sh         || exit 1
step 08_tracto      08_tracto/sift2_weights.txt        zsh $S/08_tracto.sh      || exit 1
step 09c_bundles    09_bundles/stats.tsv               zsh $S/09c_bundles.sh    || exit 1
step 11_edges       11_edges/vta_R_upper_tri_sift2.csv zsh $S/11_edges.sh       || exit 1
# résumé numérique (contrôles automatiques à relire ensuite)
$ICM/tools/.venv/bin/python $S/subject_summary.py > $T/summary.tsv 2> $LOG/summary.log
# nettoyage des intermédiaires lourds (le disque ne tient pas 13 patients complets)
setopt null_glob
rm -rf $T/03b_eddy/scratch $T/03b_synb0/OUTPUTS/*.nii.gz.tmp $T/07_5tt/scratch $T/02_denoise/dwi_den.mif $T/02_denoise/residual.mif $T/08_tracto/tracks_10M.tck \
       $T/05_03b_eddy/dwi_T1.mif $T/04_03b_eddy/dwi_unb.mif $T/03b_eddy/dwi_preproc.mif  $T/09_bundles/*.tdi.mif
echo "[$SUB] TERMINÉ $(date +%H:%M:%S)"; touch $T/DONE
