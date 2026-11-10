#!/usr/bin/env python3
"""Résumé numérique d'un patient (contrôles automatiques, TSV clé/valeur). Env : SUB, T, ICM."""
import os, subprocess, glob, json, numpy as np, nibabel as nib
SUB=os.environ['SUB']; T=os.environ['T']; ICM=os.environ.get('ICM','/Users/louan/Folder/ICM')
def sh(c):
    try: return subprocess.run(c,shell=True,capture_output=True,text=True,timeout=300).stdout.strip()
    except Exception: return ''
def p(k,v): print(f'{k}\t{v}')
p('sub',SUB)
p('dwi_shells',sh(f'mrinfo {T}/01_raw/dwi.mif -shell_bvalues -shell_sizes | tr "\\n" " "'))
g=f'{T}/../../..'  # placeholder
gc=ICM+f'/qc_cohort/{SUB}/01_raw/dwigradcheck.txt'
if os.path.exists(gc): p('dwigradcheck',open(gc).read().strip().replace('\n',' | ')[-200:])
for f,k in ((f'{T}/04_03b_eddy/mask.mif','mask_mL'),):
    if os.path.exists(f):
        a=np.asarray(nib.load(sh(f'mrconvert {f} /tmp/_m_{SUB}.nii.gz -force -quiet; echo /tmp/_m_{SUB}.nii.gz')).dataobj)>0
        p(k,round(a.sum()*np.prod(nib.load(f'/tmp/_m_{SUB}.nii.gz').header.get_zooms()[:3])/1000,1))
q=f'{ICM}/qc_cohort/{SUB}/03b_eddy/eddy_quad/qc.json'
if os.path.exists(q):
    j=json.load(open(q)); p('eddy_avg_abs_motion_mm',j.get('qc_motion_abs')); p('eddy_avg_rel_motion_mm',j.get('qc_motion_rel')); p('eddy_outlier_pct',j.get('qc_outliers_tot'))
f5=f'{T}/07_5tt/5tt_stn.mif'
if os.path.exists(f5):
    p('5tt_volumes_mL(cGM,sGM,WM,CSF)',sh(f'for i in 0 1 2 3; do mrconvert -coord 3 $i {f5} - -quiet | mrstats - -output mean -quiet; done | tr "\\n" " "'))
    p('STN_voxels_added',sh(f'mrstats {T}/07_5tt/stn_mask_T1grid.nii.gz -output sum -quiet'))
t=f'{T}/08_tracto'
if os.path.exists(t+'/sift2_mu.txt'): p('sift2_mu',open(t+'/sift2_mu.txt').read().strip())
if os.path.exists(t+'/stats.txt'): p('tracks_len_mean_median_count',' '.join(open(t+'/stats.txt').read().split('\n')[-2].split()))
for f in sorted(glob.glob(f'{T}/09_rois/*_[LR].nii.gz')):
    n=os.path.basename(f)[:-7]
    if n.endswith('_dil1') or n.startswith(('Juelich','Harvard')): continue
    p('roi_'+n+'_vox',int(np.asarray(nib.load(f).dataobj).sum()))
b=f'{T}/09_bundles/stats.tsv'
if os.path.exists(b):
    for l in open(b).read().split('\n')[1:]:
        c=l.split('\t')
        if len(c)>=5: p('bundle_'+c[0]+'_n_w_len',f'{c[1]} {c[2]} {c[4]}')
