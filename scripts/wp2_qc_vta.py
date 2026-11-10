# QC WP2 : VTA nôtre (rouge) vs auteurs (cyan), repère natif commun, sur le T1 d'ancrage des auteurs.
import nibabel as nib, numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
R='/Users/louan/Folder/ICM/'; T1=nib.load(R+'data/bids/derivatives/leaddbs/sub-DBS01/coregistration/anat/sub-DBS01_ses-preop_space-anchorNative_desc-preproc_acq-iso_T1w.nii'); V=T1.get_fdata()
fig,ax=plt.subplots(2,3,figsize=(15,10))
for r,h in enumerate('RL'):
    a=nib.load(R+f'wp2_leaddbs/compare/vta/ours_binary_{h}.nii.gz').get_fdata()>0.5; b=nib.load(R+f'wp2_leaddbs/compare/vta/theirs_binary_{h}.nii.gz').get_fdata()>0.5
    c=np.argwhere(b).mean(0).round().astype(int)
    for k,(sl,A,B,ix) in enumerate(((lambda s:V[:,:,s].T,lambda s:a[:,:,s].T,lambda s:b[:,:,s].T,(0,1,2)),(lambda s:V[:,s,:].T,lambda s:a[:,s,:].T,lambda s:b[:,s,:].T,(0,2,1)),(lambda s:V[s,:,:].T,lambda s:a[s,:,:].T,lambda s:b[s,:,:].T,(1,2,0)))):
        s=c[ix[2]]; im=sl(s); ax[r,k].imshow(im,cmap='gray',origin='lower',vmin=np.percentile(im,2),vmax=np.percentile(im,99.5))
        for m,col in ((A(s),'red'),(B(s),'cyan')):
            if m.any(): ax[r,k].contour(m.astype(float),levels=[0.5],colors=col,linewidths=1.6)
        ax[r,k].set_xlim(c[ix[0]]-45,c[ix[0]]+45); ax[r,k].set_ylim(c[ix[1]]-45,c[ix[1]]+45); ax[r,k].axis('off'); ax[r,k].set_title(f"{'droite' if h=='R' else 'gauche'} - {('axial','coronal','sagittal')[k]}  (rouge = nous, cyan = auteurs)")
plt.tight_layout(); plt.savefig(R+'qc/WP2_leaddbs/02_post/04_VTA_nous_vs_auteurs.png',dpi=100)
