#!/bin/bash
# usage : scripts/wp2_run.sh pre|post   (journal : wp2_leaddbs/logs/wp2_<stage>.log)
cd /Users/louan/Folder/ICM && /Applications/MATLAB_R2025b.app/bin/matlab -batch "addpath('/Users/louan/Folder/ICM/scripts'); wp2_run('$1'); exit" > wp2_leaddbs/logs/wp2_$1.log 2>&1
echo "exit=$?" >> wp2_leaddbs/logs/wp2_$1.log
