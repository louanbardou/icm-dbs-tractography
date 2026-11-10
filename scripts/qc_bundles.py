# QC 9c : TDI (pondérée SIFT2) de chaque faisceau, projection d'intensité maximale sur le T1, + contours des ROIs d'inclusion.
import os, nibabel as nib, numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
R=os.environ.get('ICM',os.path.dirname(os.path.dirname(os.path.abspath(__file__))))+'/'; T=R+'derivatives/tracto/'; B=T+'09_bundles/'
t1=nib.load(T+'05_ref/T1.nii.gz'); ref=nib.load(B+'cst_L.tdi.nii.gz'); V=nib.load(T+'08_tracto/tdi_sift2_1mm.mif'.replace('.mif','.mif')) if False else None
import nibabel.processing as P
T1=P.resample_from_to(t1,(ref.shape,ref.affine),order=1).get_fdata()
def tdi(n): return nib.load(B+n+'.tdi.nii.gz').get_fdata()
def roi(n): return P.resample_from_to(nib.load(T+'09_rois/'+n+'.nii.gz'),(ref.shape,ref.affine),order=0).get_fdata()>0.5
groups=[('hyperdirect','STN_motor','cortexmotor'),('stn_gpi','STN','GPi'),('cst','M1','brainstem'),('vta','VTA',None),('vta_cortexmotor','VTA','cortexmotor')]
fig,ax=plt.subplots(len(groups),4,figsize=(20,5*len(groups)))
for r,(g,a,b) in enumerate(groups):
  for c,(h,view) in enumerate([(h,v) for h in 'LR' for v in ('coronal','axial')]):
    d=tdi(f'{g}_{h}'); ctr=np.argwhere(roi(f'{a}_{h}')).mean(0).round().astype(int)
    if view=='coronal': im=T1[:,ctr[1],:].T; m=d.max(1).T; sl=[(roi(f'{x}_{h}').max(1).T,col) for x,col in ((a,'yellow'),(b,'lime')) if x and x!='brainstem']
    else: im=T1[:,:,ctr[2]].T; m=d.max(2).T; sl=[(roi(f'{x}_{h}').max(2).T,col) for x,col in ((a,'yellow'),(b,'lime')) if x and x!='brainstem']
    ax[r,c].imshow(im,cmap='gray',origin='lower',vmin=np.percentile(im,2),vmax=np.percentile(im,99.5))
    mm=np.ma.masked_less_equal(m,0); ax[r,c].imshow(mm,cmap='hot',origin='lower',alpha=0.85,vmax=np.percentile(m[m>0],99) if (m>0).any() else 1)
    for mk,col in sl: ax[r,c].contour(mk.astype(float),levels=[0.5],colors=col,linewidths=0.8)
    ax[r,c].set_title(f'{g} {h} - {view} (MIP)'); ax[r,c].axis('off')
plt.tight_layout(); plt.savefig(R+'qc/09_bundles/01_faisceaux_MIP.png',dpi=70)
# longueurs
import subprocess
fig,ax=plt.subplots(1,5,figsize=(20,3.5))
for i,(g,_,_) in enumerate(groups):
  for h,col in (('L','tab:blue'),('R','tab:red')):
    subprocess.run(['tckstats',B+f'{g}_{h}.tck','-dump','/tmp/_len.txt','-quiet','-force'],capture_output=True); out=open('/tmp/_len.txt').read().split()
    L=np.array(out,float); ax[i].hist(L,bins=40,alpha=.6,color=col,label=f'{h} (n={len(L)})')
  ax[i].set_title(g+' - longueur (mm)'); ax[i].legend()
plt.tight_layout(); plt.savefig(R+'qc/09_bundles/02_longueurs.png',dpi=80)
