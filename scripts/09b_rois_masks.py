# Étape 9b : masques ROI natifs (grille anchorNative 0,7 mm) à partir des atlas warpés + DISTAL + VTA.
import nibabel as nib, numpy as np, os, subprocess, tempfile
ANTS='antsApplyTransforms'
R=os.environ.get('ICM',os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); SUB=os.environ.get('SUB','sub-DBS01'); L=os.environ.get('L',R+'/data/bids/derivatives/leaddbs/'+SUB); O=os.environ.get('T',R+'/derivatives/tracto')+'/09_rois'
import glob
STIM=sorted(glob.glob(L+'/stimulations/native/*/'+SUB+'_sim-binary_model-simbio_hemi-L.nii'))[0].rsplit('/'+SUB,1)[0]
D=L+'/atlases/DISTAL Minimal (Ewert 2017)'
ju=nib.load(O+'/Juelich-maxprob-thr25-1mm_native.nii.gz'); J=np.asarray(ju.dataobj).astype(int)
ho=np.asarray(nib.load(O+'/HarvardOxford-cort-maxprob-thr25-1mm_native.nii.gz').dataobj).astype(int)
hs=np.asarray(nib.load(O+'/HarvardOxford-sub-maxprob-thr25-1mm_native.nii.gz').dataobj).astype(int)
aff=ju.affine
REF=L+'/coregistration/anat/'+SUB+'_ses-preop_space-anchorNative_desc-preproc_acq-iso_T1w.nii'
def onref(path):
    # rééchantillonne une image (boîte découpée ou autre grille) sur la grille T1 anchorNative, sans transformation (identité, linéaire)
    t=tempfile.mktemp(suffix='.nii.gz'); subprocess.run([ANTS,'-d','3','-i',path,'-r',REF,'-n','Linear','-o',t],check=True,capture_output=True)
    a=np.asarray(nib.load(t).dataobj); os.remove(t); return a
def save(name,m):
    nib.save(nib.Nifti1Image(m.astype(np.uint8),aff),f'{O}/{name}.nii.gz'); print(f'{name:22s} {int(m.sum()):8d} voxels ({m.sum()*0.7**3/1000:.1f} mL)')
def ctr(m): i=np.argwhere(m).mean(0); return nib.affines.apply_affine(aff,i)
# Juelich : valeur = index XML + 1 ; BA4a L/R = 46/47, BA4p = 48/49, BA6 = 90/91
m1={'L':np.isin(J,[47,49]),'R':np.isin(J,[48,50])}
ba6={'L':J==91,'R':J==92}
# SMA = Harvard-Oxford « Juxtapositional lobule » (index 25 -> 26), non latéralisée : on coupe au plan médian
sma=ho==26
stn=[onref(f'{D}/{h}/STN_motor.nii.gz') for h in ('lh','rh')]
cl=ctr(stn[0]>0.5); cr=ctr(stn[1]>0.5)
print('centre STN_motor lh / rh (mm monde):',cl.round(1),cr.round(1))
from scipy.ndimage import distance_transform_edt as edt
# hémisphère de chaque voxel SMA = côté du BA6 (déjà latéralisé) le plus proche ; robuste à une tête décentrée/inclinée
dL=edt(~ba6['L']); dR=edt(~ba6['R']); leftside=dL<dR
sma_h={'L':sma&leftside,'R':sma&~leftside}
for s in 'LR':
    save(f'M1_{s}',m1[s]); save(f'BA6_{s}',ba6[s]); save(f'SMA_{s}',sma_h[s])
    save(f'cortexmotor_{s}',m1[s]|ba6[s]|sma_h[s])
    print(s,'centre M1 (mm):',ctr(m1[s]).round(1),' | centre BA6:',ctr(ba6[s]).round(1))
    for nm,h in (('STN','STN'),('STN_motor','STN_motor'),('GPi','GPi'),('RN','RN')):
        d=D+'/'+('lh' if s=='L' else 'rh')+f'/{nm}.nii.gz'
        save(f'{nm}_{s}',onref(d)>0.5)
    v=nib.load(STIM+f'/{SUB}_sim-binary_model-simbio_hemi-{s}.nii')
    print('VTA',s,v.shape,'vs T1',J.shape); save(f'VTA_{s}',onref(STIM+f'/{SUB}_sim-binary_model-simbio_hemi-{s}.nii')>0.5)
save('brainstem',hs==8)
save('thalamus_L',hs==4); save('thalamus_R',hs==15)
