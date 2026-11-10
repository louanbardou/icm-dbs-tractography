#!/usr/bin/env python
"""QC étape 7 : 5 tissus sur le T1, interface GM/WM, noyaux sous-corticaux et STN. Usage : python qc_5tt.py dossier_07 dossier_ref dossier_qc dossier_atlases"""
import sys, os, subprocess, tempfile, numpy as np, nibabel as nib
from nibabel.processing import resample_from_to
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
D, REF, Q, ATL = sys.argv[1:5]; os.makedirs(Q, exist_ok=True); tmp = tempfile.mkdtemp()
def nii(mif):
    o = os.path.join(tmp, os.path.basename(mif) + ".nii.gz"); subprocess.run(["mrconvert", mif, o, "-force", "-quiet"], check=True); return nib.load(o)
t5 = nii(os.path.join(D, "5tt.mif")); T5 = np.asarray(t5.dataobj, np.float32); gw = np.asarray(nii(os.path.join(D, "gmwmi.mif")).dataobj, np.float32)
T1i = nib.load(os.path.join(REF, "T1.nii.gz")); T1 = np.asarray(T1i.dataobj, np.float32); bm = np.asarray(nib.load(os.path.join(REF, "T1_brain_mask.nii.gz")).dataobj) > 0
names = ["GM cortical", "GM sous-cortical", "WM", "CSF", "tissu pathologique"]
sl = lambda v, p, i: np.rot90({"x": lambda: v[i], "y": lambda: v[:, i], "z": lambda: v[:, :, i]}[p]())
stn = {}
for h in ("lh", "rh"):
    im = nib.load(os.path.join(ATL, "DISTAL Minimal (Ewert 2017)", h, "STN_motor.nii.gz")); stn[h] = np.asarray(resample_from_to(im, T1i, order=0).dataobj) > 0.5
c = np.array([np.argwhere(s).mean(0) for s in stn.values()]).mean(0).astype(int)
vm = T1[bm]; vmax = np.percentile(vm, 99.5)
# 1. chaque tissu en contour sur le T1, 2 niveaux
cols = ["lime", "yellow", "blue", "red"]
fig, ax = plt.subplots(2, 3, figsize=(17, 11))
for r, (p, i) in enumerate([("z", c[2]), ("z", c[2] + 25)]):
    ax[r, 0].imshow(sl(T1, p, i), cmap="gray", vmax=vmax); ax[r, 0].set_title(f"T1 {p}={i}")
    for k in range(4): ax[r, 1].contour(sl(T5[..., k], p, i), [0.5], colors=cols[k], linewidths=0.9)
    ax[r, 1].imshow(sl(T1, p, i), cmap="gray", vmax=vmax, alpha=0.6); ax[r, 1].set_title("contours : GM cortex (vert), GM sous-cort. (jaune), WM (bleu), CSF (rouge)")
    ax[r, 2].imshow(sl(T5[..., 2] * 1 + T5[..., 0] * 2 + T5[..., 1] * 3 + T5[..., 3] * 4, p, i), cmap="nipy_spectral"); ax[r, 2].set_title("label dominant : WM=1, GM=2, subcort=3, CSF=4")
for a in ax.flat: a.axis("off")
fig.suptitle("01 — 5 tissus : chaque tissu doit suivre sa structure sur le T1. Haut : niveau STN. Bas : 25 mm plus haut")
fig.tight_layout(); fig.savefig(os.path.join(Q, "01_tissus_sur_T1.png"), dpi=100); plt.close(fig)
# 2. noyaux gris profonds (tissu 2) et STN : coronal + axial au niveau STN
fig, ax = plt.subplots(1, 3, figsize=(17, 6))
for a, (p, i) in zip(ax, [("z", c[2]), ("y", c[1]), ("x", c[0])]):
    a.imshow(sl(T1, p, i), cmap="gray", vmax=vmax); m = sl(T5[..., 1], p, i); a.imshow(np.ma.masked_where(m < 0.3, m), cmap="autumn", alpha=0.55, vmin=0, vmax=1)
    for h, col in (("lh", "cyan"), ("rh", "magenta")):
        s = sl(stn[h].astype(float), p, i)
        if s.any(): a.contour(s, [0.5], colors=col, linewidths=1.3)
    a.axis("off"); a.set_title(f"{p}={i}")
fig.suptitle("02 — GM sous-corticale (orange) : thalamus, noyaux de la base présents ? STN_motor DISTAL en cyan (gauche) et magenta (droit). Le STN doit être sur/près d'un tissu GM sous-cortical ou à sa limite, jamais en CSF")
fig.tight_layout(); fig.savefig(os.path.join(Q, "02_GM_souscorticale_et_STN.png"), dpi=100); plt.close(fig)
# 3. interface GM/WM
fig, ax = plt.subplots(1, 3, figsize=(17, 6))
for a, (p, i) in zip(ax, [("z", c[2] + 20), ("y", c[1]), ("x", c[0] - 30)]):
    a.imshow(sl(T1, p, i), cmap="gray", vmax=vmax); g = sl(gw, p, i); a.imshow(np.ma.masked_where(g < 0.05, g), cmap="hot", alpha=0.85); a.axis("off"); a.set_title(f"{p}={i}")
fig.suptitle("03 — interface GM/WM (point de départ des streamlines, tckgen -seed_gmwmi) : ruban continu le long du cortex, sans trou")
fig.tight_layout(); fig.savefig(os.path.join(Q, "03_interface_GM_WM.png"), dpi=100); plt.close(fig)
vox = bm.sum(); print("volumes (mL, dans le masque T1) : " + ", ".join(f"{n} {T5[..., k][bm].sum() * np.prod(t5.header.get_zooms()[:3]) / 1000:.0f}" for k, n in enumerate(names)))
print("somme des 5 tissus dans le cerveau : min %.2f max %.2f" % (T5[bm].sum(-1).min(), T5[bm].sum(-1).max()))
