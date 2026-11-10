#!/usr/bin/env zsh
# Étape 0 — vérifie que tous les outils du pipeline sont présents. Usage : zsh scripts/00_env_check.sh
setopt null_glob; ok=0; ko=0
cmd(){ for c in "$@"; do if command -v $c >/dev/null 2>&1; then echo "  ok   $c"; ((ok+=1)); else echo "  KO   $c"; ((ko+=1)); fi; done }
fil(){ for f in "$@"; do if [ -e "$f" ]; then echo "  ok   $f"; ((ok+=1)); else echo "  KO   $f"; ((ko+=1)); fi; done }
echo "MRtrix3";  cmd mrconvert mrview dwidenoise mrdegibbs tckgen tcksift2 dwifslpreproc dwigradcheck dwibiascorrect dwi2response 5ttgen
echo "FSL ($FSLDIR)"; cmd bet eddy_cpu topup fslmaths fsleyes
echo "ANTs ($ANTSPATH)"; cmd antsRegistration N4BiasFieldCorrection antsApplyTransforms
echo "Docker"; cmd docker
echo "MATLAB"; m=(/Applications/MATLAB_R20*.app); [ ${#m} -gt 0 ] && { echo "  ok   $m"; ((ok+=1)); } || { echo "  KO   MATLAB (non installé)"; ((ko+=1)); }
echo "Lead-DBS / SPM12"; fil /Users/louan/opt/leaddbs/lead.m /Users/louan/opt/spm12/spm.m
echo "Python venv"; /Users/louan/Folder/ICM/tools/.venv/bin/python -c "import nibabel, numpy, scipy, h5py, matplotlib" 2>/dev/null && { echo "  ok   nibabel numpy scipy h5py matplotlib"; ((ok+=1)); } || { echo "  KO   venv python packages"; ((ko+=1)); }
echo "Données"; fil /Users/louan/Folder/ICM/data/bids/sub-DBS01/ses-preop/dwi/sub-DBS01_ses-preop_dwi.nii.gz
echo "---- $ok ok, $ko KO"
