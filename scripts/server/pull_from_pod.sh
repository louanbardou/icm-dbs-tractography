#!/bin/bash
# Rapatrie depuis le pod les résultats légers des patients terminés (DONE) : résumé, faisceaux, arêtes, ROI, QC. Usage : bash scripts/pull_from_pod.sh
ICM=${ICM:?définir ICM}; SSHO="ssh -i $HOME/.ssh/runpod_icm -o StrictHostKeyChecking=no -p ${POD_PORT:?set POD_PORT}"; H=root@${POD_IP:?set POD_IP}
for s in $($SSHO $H 'ls /work/ICM/derivatives/cohort/*/DONE 2>/dev/null' | sed 's#.*/cohort/\(sub-[A-Z0-9]*\)/DONE#\1#'); do
  mkdir -p $ICM/derivatives/cohort/$s $ICM/qc_cohort/$s
  rsync -az -e "$SSHO" --include='*upper_tri*.csv' --exclude='scratch' --exclude='*.tck' --exclude='*.mif' --exclude='*_sift2.csv' --exclude='*_count.csv' --include='*/' --include='summary.tsv' --include='stats.tsv' --include='stats.txt' --include='sift2_*.txt' --include='11_edges/**' --include='09_bundles/**' --include='09_rois/*.nii.gz' --include='log/**' --include='DONE' --exclude='*' $H:/work/ICM/derivatives/cohort/$s/ $ICM/derivatives/cohort/$s/
  rsync -az -e "$SSHO" $H:/work/ICM/qc_cohort/$s/ $ICM/qc_cohort/$s/ 2>/dev/null
  echo "$s rapatrié"
done
