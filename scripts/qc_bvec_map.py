#!/usr/bin/env python
"""Contrôle visuel des gradients : (1) directions bvec sur la sphère par shell, (2) carte FA colorée par direction (DEC).
Usage : python qc_bvec_map.py dwi.mif mask.mif qc_dir"""
import sys, os, subprocess, tempfile
import numpy as np, nibabel as nib
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
dwi, mask, qc = sys.argv[1:4]; os.makedirs(qc, exist_ok=True); tmp = tempfile.mkdtemp()
run = lambda *a: subprocess.run(a, check=True, capture_output=True)
# --- 1. gradients en repère scanner (mrinfo -dwgrad : x y z b)
g = np.loadtxt(subprocess.run(["mrinfo", dwi, "-dwgrad"], capture_output=True, text=True, check=True).stdout.split("\n") and
               __import__("io").StringIO(subprocess.run(["mrinfo", dwi, "-dwgrad"], capture_output=True, text=True, check=True).stdout))
b = np.round(g[:, 3] / 100) * 100; v = g[:, :3]; n = np.linalg.norm(v, axis=1)
sh = [s for s in np.unique(b) if s > 50]
fig = plt.figure(figsize=(17, 5.5))
col = {1000: "tab:blue", 2000: "tab:red"}
ax = fig.add_subplot(1, 4, 1, projection="3d")
for s in sh:
    m = (b == s) & (n > 0); u = v[m] / n[m, None]
    for sgn, alpha in [(1, 1.0), (-1, 0.25)]:
        ax.scatter(*(sgn * u).T, c=col.get(s, "k"), s=18, alpha=alpha, label=f"b={int(s)}" if sgn == 1 else None)
ax.set_xlabel("x (G-D)"); ax.set_ylabel("y (P-A)"); ax.set_zlabel("z (I-S)"); ax.set_title("directions sur la sphère\n(pleins = bvec, pâles = antipodes)"); ax.legend(loc="upper left", fontsize=8)
for k, (i, j, nm) in enumerate([(0, 1, "x–y (axial)"), (0, 2, "x–z (coronal)"), (1, 2, "y–z (sagittal)")]):
    a = fig.add_subplot(1, 4, k + 2)
    for s in sh:
        m = (b == s) & (n > 0); u = v[m] / n[m, None]
        for sgn, alpha in [(1, 1.0), (-1, 0.25)]: a.scatter(sgn * u[:, i], sgn * u[:, j], c=col.get(s, "k"), s=14, alpha=alpha)
    a.add_patch(plt.Circle((0, 0), 1, fill=False, color="gray")); a.set_aspect("equal"); a.set_xlim(-1.1, 1.1); a.set_ylim(-1.1, 1.1); a.set_title(f"projection {nm}")
fig.suptitle("06 — répartition des gradients : 40 directions par shell doivent couvrir la sphère de façon homogène, sans trou ni amas ; b0 = {} volume(s)".format(int((b <= 50).sum())))
fig.tight_layout(); fig.savefig(os.path.join(qc, "06_bvec_sphere.png"), dpi=105); plt.close(fig)
for s in sh:
    m = (b == s) & (n > 0); u = v[m] / n[m, None]; c = u @ u.T; np.fill_diagonal(c, 0)
    print(f"b={int(s)} : {m.sum()} directions, norme moy. {n[m].mean():.3f}, angle min entre deux directions {np.degrees(np.arccos(np.abs(c).max())):.1f}°")
# --- 2. DEC : tenseur sur b0 + b1000, direction principale en repère scanner, couleur = |v|, luminosité = FA
sub = os.path.join(tmp, "dwi_b1000.mif"); ten = os.path.join(tmp, "dt.mif")
run("dwiextract", dwi, sub, "-shells", "0,1000", "-force"); run("dwi2tensor", sub, ten, "-mask", mask, "-force")
run("tensor2metric", ten, "-fa", os.path.join(tmp, "fa.nii.gz"), "-vector", os.path.join(tmp, "ev.nii.gz"), "-force")
fa = nib.load(os.path.join(tmp, "fa.nii.gz")).get_fdata(); ev = nib.load(os.path.join(tmp, "ev.nii.gz")).get_fdata()
fa = np.clip(np.nan_to_num(fa), 0, 1); rgb = np.clip(np.abs(np.nan_to_num(ev)) * fa[..., None], 0, 1)
fig, ax = plt.subplots(1, 3, figsize=(17, 6)); zooms = nib.load(os.path.join(tmp, "fa.nii.gz")).header.get_zooms()
X, Y, Z = (np.array(fa.shape) * [0.5, 0.5, 0.5]).astype(int)
Z = int(fa.shape[2] * 0.62)
for a, (im, t, asp) in zip(ax, [(rgb[:, :, Z], "axial (corps calleux, CST)", zooms[1] / zooms[0]), (rgb[:, Y], "coronal", zooms[2] / zooms[0]), (rgb[X], "sagittal", zooms[2] / zooms[1])]):
    a.imshow(np.rot90(im), aspect=asp); a.set_title(t); a.axis("off")
fig.suptitle("07 — FA colorée par direction (rouge = gauche-droite, vert = avant-arrière, bleu = haut-bas). Attendu : corps calleux ROUGE, faisceau cortico-spinal BLEU, cingulum / faisceau longitudinal VERT")
fig.tight_layout(); fig.savefig(os.path.join(qc, "07_dec_fa.png"), dpi=105); plt.close(fig)
print("QC écrit dans", qc)
