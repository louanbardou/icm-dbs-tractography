#!/usr/bin/env zsh
# Lance le pipeline sur tous les patients restants, l'un après l'autre (le disque et le CPU ne permettent pas mieux). Attend le téléchargement de chaque patient.
# Usage : zsh scripts/run_cohort.sh [sub-DBS02 ...]    (par défaut : 02 à 14)
ICM=/Users/louan/Folder/ICM; subs=("$@"); [[ ${#subs} -eq 0 ]] && subs=(sub-DBS02 sub-DBS03 sub-DBS04 sub-DBS05 sub-DBS06 sub-DBS07 sub-DBS08 sub-DBS09 sub-DBS10 sub-DBS11 sub-DBS12 sub-DBS13 sub-DBS14)
for s in $subs; do
  until grep -qh "^$s: OK" $ICM/logs/10_download.log $ICM/logs/10_download_rest.log 2>/dev/null; do sleep 30; done
  zsh $ICM/scripts/run_subject.sh $s >> $ICM/logs/cohort_$s.log 2>&1 || echo "$s ÉCHEC, on passe au suivant" >> $ICM/logs/cohort_summary.log
  echo "$s fini $(date +%H:%M) $( [[ -e $ICM/derivatives/cohort/$s/DONE ]] && echo OK || echo ÉCHEC)" >> $ICM/logs/cohort_summary.log
done
