#!/usr/bin/env zsh
# Étape 9c — extraction de faisceaux DBS depuis la tractographie globale (tracks_10M + poids SIFT2), par hémisphère.
# Faisceaux : hyperdirecte (STN_motor <-> cortex moteur), STN-GPi, CST (M1 <-> tronc), fibres du VTA (toutes, et VTA <-> cortex moteur).
# Usage : zsh scripts/09c_bundles.sh   (une lecture de 4,5 Go par faisceau)
set -e; set -o pipefail
ICM=${ICM:-${0:A:h:h}}; T=${T:-$ICM/derivatives/tracto}; R=$T/09_rois; O=$T/09_bundles; TR=$T/08_tracto
mkdir -p $O
for n in STN_L STN_R STN_motor_L STN_motor_R; do [ -f $R/${n}_dil1.nii.gz ] || maskfilter -quiet -force $R/$n.nii.gz dilate -npass 1 $R/${n}_dil1.nii.gz; done
W=(-tck_weights_in $TR/sift2_weights.txt)
oth(){ [[ $1 == L ]] && echo R || echo L; }
ext(){ # nom, args tckedit...
  n=$1; shift
  tckedit $TR/tracks_10M.tck $O/$n.tck "${W[@]}" -tck_weights_out $O/$n.w.txt "$@" -nthreads 8 -force -quiet
  tckmap $O/$n.tck -tck_weights_in $O/$n.w.txt -template $T/05_ref/T1.nii.gz -vox 1 $O/$n.tdi.mif -force -quiet
}
# v2 (après rejet de la v1 « la streamline touche les ROIs », qui mélangeait CST/tronc avec l'hyperdirecte) :
#  hyperdirecte et STN-GPi : -ends_only (les extrémités doivent tomber dans les ROIs, STN dilaté de 1 voxel car l'ACT s'arrête à l'interface GM) + exclusion du tronc.
#  CST et VTA : inchangés. VTA-cortex moteur : exclusion du tronc.
for h in L R; do o=$(oth $h)
  echo "== $h hyperdirecte  $(date +%H:%M:%S)"; ext hyperdirect_$h -ends_only -include $R/STN_motor_${h}_dil1.nii.gz -include $R/cortexmotor_$h.nii.gz -exclude $R/brainstem.nii.gz -exclude $R/STN_$o.nii.gz -exclude $R/cortexmotor_$o.nii.gz
  echo "== $h STN-GPi       $(date +%H:%M:%S)"; ext stn_gpi_$h -ends_only -include $R/STN_${h}_dil1.nii.gz -include $R/GPi_$h.nii.gz -exclude $R/brainstem.nii.gz -exclude $R/STN_$o.nii.gz -exclude $R/GPi_$o.nii.gz
  echo "== $h CST           $(date +%H:%M:%S)"; ext cst_$h -include $R/M1_$h.nii.gz -include $R/brainstem.nii.gz -exclude $R/cortexmotor_$o.nii.gz
  echo "== $h VTA (tout)    $(date +%H:%M:%S)"; ext vta_$h -include $R/VTA_$h.nii.gz -exclude $R/VTA_$o.nii.gz
  echo "== $h VTA-cortex mot $(date +%H:%M:%S)"; ext vta_cortexmotor_$h -include $R/VTA_$h.nii.gz -include $R/cortexmotor_$h.nii.gz -exclude $R/brainstem.nii.gz -exclude $R/cortexmotor_$o.nii.gz
done
echo "== stats $(date +%H:%M:%S)"
O=$O TR=$TR python3 - <<'PY'
import numpy as np, glob, os, subprocess
O=os.environ['O']; Wt=np.loadtxt(os.environ['TR']+'/sift2_weights.txt'); tot=Wt.sum()
rows=['faisceau\tn_streamlines\tpoids_SIFT2\t%_poids_total\tlongueur_moy_mm']
for f in sorted(glob.glob(O+'/*.tck')):
    n=os.path.basename(f)[:-4]; w=np.loadtxt(f'{O}/{n}.w.txt',ndmin=1)
    s=subprocess.run(['tckstats',f,'-output','mean','-quiet'],capture_output=True,text=True).stdout.strip() or 'nan'
    rows.append(f'{n}\t{len(w)}\t{w.sum():.2f}\t{100*w.sum()/tot:.4f}\t{float(s):.1f}')
open(O+'/stats.tsv','w').write('\n'.join(rows)+'\n'); print('\n'.join(rows))
PY
