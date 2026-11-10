#!/bin/bash
cd /Users/louan/Folder/ICM && /Applications/MATLAB_R2025b.app/bin/matlab -batch "addpath('/Users/louan/Folder/ICM/scripts'); wp2_vta; exit" > wp2_leaddbs/logs/wp2_vta.log 2>&1
echo "exit=$?" >> wp2_leaddbs/logs/wp2_vta.log
