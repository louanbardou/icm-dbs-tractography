#!/usr/bin/env python
"""QC étape 5 : damier T1/b0, contours STN_motor (DISTAL) et masque T1 sur le b0 recalé, Dice des masques.
Usage : python qc_coreg.py dossier_ref dossier_05 dossier_qc dossier_atlases"""
import sys, os, json, numpy as np, nibabel as nib
from nibabel.processing import resample_from_to
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
REF, D, Q, ATL = sys.argv[1:5]; os.makedirs(Q, exist_ok=True)
T1i = nib.load(os.path.join(REF, "T1.nii.gz")); T1 = np.asarray(T1i.dataobj, np.float32)
T1m = np.asarray(nib.load(os.path.join(REF, "T1_brain_mask.nii.gz")).dataobj) > 0
b0 = np.asarray(nib.load(os.path.join(D, "b0_in_T1.nii.gz")).dataobj, np.float32)
dm = np.asarray(nib.load(os.path.join(D, "mask_in_T1grid.nii.gz")).dataobj) > 0
dice = 2 * (dm & T1m).sum() / (dm.sum() + T1m.sum())
atl = os.path.join(ATL, "DISTAL Minimal (Ewert 2017)")
stn = {}
for h in ("lh", "rh"):
    im = nib.load(os.path.join(atl, h, "STN_motor.nii.gz")); stn[h] = np.asarray(resample_from_to(im, T1i, order=0).dataobj) > 0.5
c = np.array([np.argwhere(s).mean(0) for s in stn.values()]).mean(0).astype(int)   # centre des deux STN dans la grille T1
sl = lambda v, p, i: np.rot90({"x": lambda: v[i], "y": lambda: v[:, i], "z": lambda: v[:, :, i]}[p]())
nrm = lambda v: v / np.percentile(v[T1m], 99)
# 1. damier sur le niveau du STN
fig, ax = plt.subplots(1, 3, figsize=(17, 6)); T = nrm(T1); B = nrm(b0)
for a, (p, i) in zip(ax, [("z", c[2]), ("y", c[1]), ("x", c[0])]):
    t, b = sl(T, p, i), sl(B, p, i); yy, xx = np.indices(t.shape); k = ((yy // 14 + xx // 14) % 2).astype(bool)
    a.imshow(np.where(k, np.clip(t, 0, 1.2), np.clip(b, 0, 1.2)), cmap="gray"); a.axis("off"); a.set_title(f"{p} = {i} (niveau STN)")
fig.suptitle("01 — damier T1 / b0 recalé au niveau du STN : les bords (ventricules, contour du cerveau, tronc) doivent se prolonger d'une case à l'autre")
fig.tight_layout(); fig.savefig(os.path.join(Q, "01_damier_T1_b0.png"), dpi=100); plt.close(fig)
# 2. contours STN (DISTAL) + contour masque cerveau T1 sur le b0, 2 niveaux
fig, ax = plt.subplots(2, 3, figsize=(17, 11))
for r, dz in enumerate([0, 14]):
    for a, (p, i) in zip(ax[r], [("z", c[2] + dz), ("y", c[1]), ("x", c[0])]):
        a.imshow(sl(B, p, i), cmap="gray", vmax=1.0); a.axis("off")
        a.contour(sl(T1m.astype(float), p, i), [0.5], colors="cyan", linewidths=0.7)
        for h, col in (("lh", "r"), ("rh", "yellow")):
            if sl(stn[h].astype(float), p, i).any(): a.contour(sl(stn[h].astype(float), p, i), [0.5], colors=col, linewidths=1.2)
        a.set_title(f"{p} = {i}")
fig.suptitle("02 — b0 recalé + contour du cerveau T1 (cyan) + STN_motor DISTAL gauche (rouge) et droit (jaune). Haut : niveau STN. Bas : 14 mm plus haut")
fig.tight_layout(); fig.savefig(os.path.join(Q, "02_stn_et_cerveau_sur_b0.png"), dpi=100); plt.close(fig)
# 3. zoom frontal (là où la correction de susceptibilité joue) : sagittal médian
i = c[0]; fig, ax = plt.subplots(1, 2, figsize=(14, 6))
for a, (v, t) in zip(ax, [(B, "b0 recalé"), (T, "T1")]):
    a.imshow(sl(v, "x", i), cmap="gray", vmax=1.1); a.axis("off"); a.set_title(t)
    a.contour(sl(T1m.astype(float), "x", i), [0.5], colors="cyan", linewidths=0.7); a.contour(sl(dm.astype(float), "x", i), [0.5], colors="red", linewidths=0.7)
fig.suptitle("03 — sagittal : contour masque T1 (cyan) vs masque DWI recalé (rouge) — écarts frontaux = distorsion résiduelle")
fig.tight_layout(); fig.savefig(os.path.join(Q, "03_sagittal_frontal.png"), dpi=100); plt.close(fig)
json.dump({"dice_masque_dwi_vs_T1": float(dice), "centre_STN_voxel_T1": [int(x) for x in c]}, open(os.path.join(Q, "metriques.json"), "w"), indent=1)
print(f"Dice masque DWI recalé / masque cerveau T1 : {dice:.3f} ; centre STN (voxels T1) {c.tolist()}")
