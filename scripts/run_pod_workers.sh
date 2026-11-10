#!/usr/bin/env zsh
# Sur le pod : 3 files de patients en parallèle (Synb0 est sérialisé par un verrou). Usage : zsh scripts/run_pod_workers.sh
ICM=/work/ICM
w() { for s in "$@"; do
  until grep -q "^$s: OK" $ICM/logs/10_download_pod.log; do sleep 20; done
  zsh $ICM/scripts/run_subject.sh $s >> $ICM/logs/cohort_$s.log 2>&1; echo "$s fini $(date +%H:%M) $( [[ -e $ICM/derivatives/cohort/$s/DONE ]] && echo OK || echo ÉCHEC)" >> $ICM/logs/cohort_summary_pod.log
done; }
w sub-DBS06 sub-DBS09 sub-DBS13 &
w sub-DBS07 sub-DBS10 sub-DBS14 &
w sub-DBS08 sub-DBS12 &
wait
