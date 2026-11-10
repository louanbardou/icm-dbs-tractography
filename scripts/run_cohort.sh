#!/usr/bin/env zsh
# Run the per-subject pipeline on a list of subjects, N at a time (default 1).
# Usage: JOBS=3 zsh scripts/run_cohort.sh sub-01 sub-02 sub-03 ...
# Each subject writes derivatives/cohort/<sub>/ and logs/cohort_<sub>.log; failures are listed in logs/cohort_summary.log and do not stop the others.
# A subject that already has a DONE file is skipped; one that is currently running is skipped too (lock directory).
ICM=${ICM:-${0:A:h:h}}; export ICM; mkdir -p $ICM/logs
(( $# )) || { echo "usage: zsh scripts/run_cohort.sh sub-xx [sub-yy ...]"; exit 1; }
one() { s=$1; zsh $ICM/scripts/run_subject.sh $s >> $ICM/logs/cohort_$s.log 2>&1
        echo "$s $(date +%F_%H:%M) $( [[ -e $ICM/derivatives/cohort/$s/DONE ]] && echo OK || echo FAILED )" >> $ICM/logs/cohort_summary.log; }
n=0; for s in "$@"; do one $s & (( ++n % ${JOBS:-1} == 0 )) && wait; done; wait
