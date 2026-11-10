#!/usr/bin/env zsh
# Relance tractographie + arêtes pour des patients déjà traités dont tracks_10M.tck a été supprimé. Usage : zsh scripts/redo_tracto_edges.sh sub-DBS02 sub-DBS03
ICM=/Users/louan/Folder/ICM
for s in "$@"; do
  export SUB=$s T=$ICM/derivatives/cohort/$s QCR=$ICM/qc_cohort/$s L=$ICM/data/bids/derivatives/leaddbs/$s
  zsh $ICM/scripts/08_tracto.sh > $T/log/08_tracto_redo.log 2>&1 && zsh $ICM/scripts/11_edges.sh > $T/log/11_edges.log 2>&1 && rm -f $T/08_tracto/tracks_10M.tck && echo "$s edges OK $(date +%H:%M)" >> $ICM/logs/cohort_summary.log || echo "$s redo ÉCHEC" >> $ICM/logs/cohort_summary.log
done
