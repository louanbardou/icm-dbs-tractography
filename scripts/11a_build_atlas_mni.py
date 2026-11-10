#!/usr/bin/env python3
"""Atlas de parcellation en MNI152NLin2009b (grille 1 mm) : Glasser HCP-MMP1 volumique (360 corticaux, gauche/droite séparés par le signe de x)
+ Melbourne/Tian (14 sous-corticaux par hémisphère). Les régions Tian écrasent Glasser là où ils se recouvrent. Le STN est ajouté par patient (étape 11)."""
import nibabel as nb, numpy as np, os, subprocess, sys
ICM = os.environ.get('ICM', '/Users/louan/Folder/ICM'); O = f'{ICM}/data/atlases'; os.makedirs(O, exist_ok=True)
ref = nb.load(f'{ICM}/derivatives/cohort/_shared/fsl2009b/t1_mni2009b_1mm.nii.gz')
shape, aff = ref.shape, ref.affine
def resamp(img, order=0):
    from nibabel.processing import resample_from_to
    return np.rint(resample_from_to(img, (shape, aff), order=0).get_fdata()).astype(np.int32)
g = resamp(nb.load(f'{O}/glasser/glasser.nii.gz'))
ijk = np.indices(shape).reshape(3, -1).T; x = nb.affines.apply_affine(aff, ijk)[:, 0].reshape(shape)
lab = np.zeros(shape, np.int32); names = {}
for i in range(1, 181):
    n = open(f'{O}/glasser/glasser_labels.txt').read().split('\n')[i-1].split()[1].replace('L_', '').replace('_ROI', '')
    names[i] = 'L_' + n; names[i + 180] = 'R_' + n
lab[(g > 0) & (x <= 0)] = g[(g > 0) & (x <= 0)]; lab[(g > 0) & (x > 0)] = g[(g > 0) & (x > 0)] + 180
T = '/Users/louan/opt/leaddbs/templates/space/MNI152NLin2009bAsym/atlases/Melbourne Subcortex Atlas (Tian 2020)'
parts = ['aCAU', 'pCAU', 'aPUT', 'pPUT', 'aGP', 'pGP', 'aTHA', 'pTHA', 'NAc', 'aHIP', 'pHIP', 'lAMY', 'mAMY']
k = 360
for h, H in (('lh', 'L'), ('rh', 'R')):
    for p in parts:
        k += 1; m = resamp(nb.load(f'{T}/{h}/{p}.nii.gz')) > 0; lab[m] = k; names[k] = f'{H}_{p}'
nb.save(nb.Nifti1Image(lab, aff), f'{O}/parc_mni2009b_1mm.nii.gz')
with open(f'{O}/parc_labels.tsv', 'w') as f:
    f.write('index\tname\n'); [f.write(f'{i}\t{names[i]}\n') for i in sorted(names)]
print('nœuds', len(names), '(+ STN_L/STN_R ajoutés par patient, indices', k + 1, k + 2, ')')
