#!/usr/bin/env python
"""QC étape 4 : contour du masque dwi2mask (rouge) et bet (vert) sur le b0, carte de biais. Usage : python qc_mask.py dossier_04 dossier_qc"""
import sys, os, subprocess, numpy as np, nibabel as nib
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
D, Q = sys.argv[1:3]; os.makedirs(Q, exist_ok=True)
ld = lambda p: np.asarray(nib.load(os.path.join(D, p)).dataobj, dtype=np.float32)
b0, m1, m2 = ld("b0.nii.gz"), ld("mask.nii.gz") > 0.5, ld("b0_bet_mask.nii.gz") > 0.5
dice = 2 * (m1 & m2).sum() / (m1.sum() + m2.sum())
sl = lambda v, p, i: np.rot90({"x": lambda: v[i], "y": lambda: v[:, i], "z": lambda: v[:, :, i]}[p]())
fig, ax = plt.subplots(3, 4, figsize=(17, 11))
for r, p in enumerate("zyx"):
    n = b0.shape["xyz".index(p)]
    for c, f in enumerate([0.3, 0.45, 0.6, 0.75] if p == "z" else [0.35, 0.5, 0.6, 0.7]):
        i = int(f * (n - 1)); a = ax[r, c]; a.imshow(sl(b0, p, i), cmap="gray", vmax=np.percentile(b0, 99.5)); a.axis("off")
        a.contour(sl(m1.astype(float), p, i), [0.5], colors="r", linewidths=0.8); a.contour(sl(m2.astype(float), p, i), [0.5], colors="lime", linewidths=0.8, linestyles="dashed")
        a.set_title(f"{p} = {i}", fontsize=9)
fig.suptitle(f"01 — masque dwi2mask (rouge) vs bet sur b0 (vert pointillé) — Dice {dice:.3f}, {int(m1.sum())} / {int(m2.sum())} voxels. Pas de trou dans pallidum/thalamus, pas d'orbite")
fig.tight_layout(); fig.savefig(os.path.join(Q, "01_masque_contours.png"), dpi=100); plt.close(fig)
subprocess.run(["mrconvert", os.path.join(D, "bias.mif"), os.path.join(D, "bias.nii.gz"), "-force", "-quiet"], check=True)
bi = ld("bias.nii.gz")
if bi.ndim == 4: bi = bi[..., 0]
fig, ax = plt.subplots(1, 3, figsize=(14, 4.5)); inb = bi[m1]
for a, p in zip(ax, "zyx"):
    i = b0.shape["xyz".index(p)] // 2; im = a.imshow(sl(np.where(m1, bi, np.nan), p, i), cmap="viridis"); a.axis("off"); a.set_title(p)
fig.colorbar(im, ax=ax, shrink=0.8); fig.suptitle(f"02 — champ de biais (multiplicatif) dans le masque : min {inb.min():.2f}, médiane {np.median(inb):.2f}, max {inb.max():.2f} — doit être lisse, 0,7 à 1,4 environ")
fig.savefig(os.path.join(Q, "02_champ_biais.png"), dpi=100, bbox_inches="tight"); plt.close(fig)
print(f"Dice dwi2mask/bet {dice:.3f} ; biais min {inb.min():.2f} med {np.median(inb):.2f} max {inb.max():.2f}")
