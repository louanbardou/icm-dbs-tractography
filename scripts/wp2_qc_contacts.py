# QC WP2 : nos contacts PaCER (coords natives) superposés au CT recalé (brainshift), 3 plans par côté.
import nibabel as nib, numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, sys
D='/Users/louan/Folder/ICM/wp2_leaddbs/derivatives/leaddbs/sub-DBS01/'
S='/private/tmp/claude-501/-Users-louan-Folder-ICM/1d5275af-dd37-471a-8bdd-2ece49166f92/scratchpad/'
ct=nib.load(D+'brainshift/anat/sub-DBS01_ses-postop_space-anchorNative_rec-tonemappedbrainshift_desc-preproc_CT.nii') if False else None
import glob
f=[p for p in glob.glob(D+'**/*space-anchorNative*rec-tonemappedbrainshift*CT.nii',recursive=True)]+[p for p in glob.glob(D+'coregistration/anat/*CT.nii')]
print(f); ct=nib.load(f[0]); V=ct.get_fdata(); inv=np.linalg.inv(ct.affine)
fig,ax=plt.subplots(2,3,figsize=(15,10))
for r,(s,nm) in enumerate(((1,'droite'),(2,'gauche'))):
    c=np.loadtxt(S+f'ours_native_{s}.txt',delimiter=','); vox=nib.affines.apply_affine(inv,c); m=vox.mean(0).round().astype(int)
    for k,(sl,lab,a,b) in enumerate(((V[:,:,m[2]].T,'axial',0,1),(V[:,m[1],:].T,'coronal',0,2),(V[m[0],:,:].T,'sagittal',1,2))):
        w=sl[(sl>-100)&(sl<3000)]; ax[r,k].imshow(sl,cmap='gray',origin='lower',vmin=np.percentile(w,5),vmax=np.percentile(w,99.8))
        ax[r,k].plot(vox[:,a],vox[:,b],'r+',ms=12); ax[r,k].set_xlim(vox[:,a].mean()-40,vox[:,a].mean()+40); ax[r,k].set_ylim(vox[:,b].mean()-40,vox[:,b].mean()+40)
        ax[r,k].set_title(f'{nm} - {lab}'); ax[r,k].axis('off')
plt.tight_layout(); plt.savefig('/Users/louan/Folder/ICM/qc/WP2_leaddbs/02_post/03_contacts_PaCER_sur_CT.png',dpi=110)
