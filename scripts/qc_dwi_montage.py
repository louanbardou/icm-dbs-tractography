#!/usr/bin/env python
"""Montages QC d'une DWI : b0/b1000/b2000 en 3 plans, mosaïque de tous les volumes, intensité moyenne par volume.
Usage : python qc_dwi_montage.py dwi.mif qc_dir
"""
import sys, os, subprocess, tempfile
import numpy as np, nibabel as nib
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

mif, qc = sys.argv[1], sys.argv[2]
os.makedirs(qc, exist_ok=True)
tmp = tempfile.mkdtemp()
nii = os.path.join(tmp, "dwi.nii.gz"); bval = os.path.join(tmp, "dwi.bval"); bvec = os.path.join(tmp, "dwi.bvec")
subprocess.run(["mrconvert", mif, nii, "-export_grad_fsl", bvec, bval, "-quiet", "-force"], check=True)
img = nib.load(nii); d = np.asarray(img.dataobj, dtype=np.float32); b = np.loadtxt(bval)
zoom = img.header.get_zooms()[:3]
X, Y, Z, N = d.shape

def shell_mean(bv): return d[..., np.isclose(b, bv, atol=50)].mean(-1)
vols = {"b0": shell_mean(0), "b1000": shell_mean(1000), "b2000": shell_mean(2000)}

# 1) trois plans × trois shells
fig, ax = plt.subplots(3, 3, figsize=(12, 12))
for i, (name, v) in enumerate(vols.items()):
    vmax = np.percentile(v[v > 0], 99)
    ax[i, 0].imshow(v[:, :, Z // 2].T, cmap="gray", origin="lower", vmax=vmax, aspect=zoom[1] / zoom[0])
    ax[i, 1].imshow(v[:, Y // 2, :].T, cmap="gray", origin="lower", vmax=vmax, aspect=zoom[2] / zoom[0])
    ax[i, 2].imshow(v[X // 2, :, :].T, cmap="gray", origin="lower", vmax=vmax, aspect=zoom[2] / zoom[1])
    ax[i, 0].set_ylabel(name, fontsize=14)
for a in ax.flat: a.set_xticks([]); a.set_yticks([])
ax[0, 0].set_title("axial"); ax[0, 1].set_title("coronal"); ax[0, 2].set_title("sagittal")
fig.suptitle("Moyenne par shell — chercher : saturation du b0, signal frontal/temporal, symétrie"); fig.tight_layout()
fig.savefig(os.path.join(qc, "01_shells_3plans.png"), dpi=110); plt.close(fig)

# 2) mosaïque : tous les volumes à la coupe axiale médiane
cols = 9; rows = int(np.ceil(N / cols))
fig, ax = plt.subplots(rows, cols, figsize=(cols * 1.8, rows * 1.9))
for i in range(rows * cols):
    a = ax.flat[i]; a.axis("off")
    if i < N:
        sl = d[:, :, Z // 2, i]; a.imshow(sl.T, cmap="gray", origin="lower", vmax=np.percentile(sl, 99.5), aspect=zoom[1] / zoom[0])
        a.set_title(f"{i} b{int(b[i])}", fontsize=7)
fig.suptitle("Tous les volumes, coupe axiale médiane — chercher : volumes sombres, rayures, décalages"); fig.tight_layout()
fig.savefig(os.path.join(qc, "02_mosaique_volumes.png"), dpi=100); plt.close(fig)

# 3) mosaïque sagittale (dropouts de coupe = bandes horizontales)
fig, ax = plt.subplots(rows, cols, figsize=(cols * 1.6, rows * 2.0))
for i in range(rows * cols):
    a = ax.flat[i]; a.axis("off")
    if i < N:
        sl = d[X // 2, :, :, i]; a.imshow(sl.T, cmap="gray", origin="lower", vmax=np.percentile(sl, 99.5), aspect=zoom[2] / zoom[1])
        a.set_title(f"{i}", fontsize=7)
fig.suptitle("Tous les volumes, coupe sagittale médiane — chercher : bandes horizontales noires (dropout de coupe)"); fig.tight_layout()
fig.savefig(os.path.join(qc, "03_mosaique_sagittal.png"), dpi=100); plt.close(fig)

# 4) intensité moyenne par volume (dans un masque grossier) et par coupe
mask = vols["b0"] > np.percentile(vols["b0"], 60)
mean_vol = np.array([d[..., i][mask].mean() for i in range(N)])
fig, ax = plt.subplots(2, 1, figsize=(12, 7))
for bv, c in [(0, "k"), (1000, "tab:blue"), (2000, "tab:red")]:
    idx = np.isclose(b, bv, atol=50); ax[0].plot(np.where(idx)[0], mean_vol[idx], "o", c=c, label=f"b{bv}")
ax[0].set_xlabel("volume"); ax[0].set_ylabel("signal moyen (masque)"); ax[0].legend(); ax[0].set_title("Signal moyen par volume — un point isolé bas = volume suspect")
slice_mean = np.array([[d[:, :, z, i][mask[:, :, z]].mean() if mask[:, :, z].any() else np.nan for z in range(Z)] for i in range(N)])
norm = np.full_like(slice_mean, np.nan)
for bv in (0, 1000, 2000):  # normaliser chaque coupe par la médiane de SON shell
    idx = np.isclose(b, bv, atol=50)
    if idx.sum() > 1: norm[idx] = slice_mean[idx] / np.nanmedian(slice_mean[idx], axis=0, keepdims=True)
    else: norm[idx] = 1.0
im = ax[1].imshow(norm.T, aspect="auto", cmap="RdBu_r", vmin=0.6, vmax=1.4, origin="lower")
ax[1].set_xlabel("volume"); ax[1].set_ylabel("coupe z"); ax[1].set_title("Signal par coupe, normalisé par volume — un pixel bleu foncé = dropout de coupe")
plt.colorbar(im, ax=ax[1]); fig.tight_layout()
fig.savefig(os.path.join(qc, "04_signal_par_volume_et_coupe.png"), dpi=110); plt.close(fig)

suspect = np.where(np.nan_to_num(norm, nan=1.0) < 0.7)
with open(os.path.join(qc, "04_dropouts_suspects.txt"), "w") as f:
    f.write(f"{len(suspect[0])} couples (volume, coupe) avec signal < 70 % de la médiane\n")
    for v, z in zip(*suspect): f.write(f"vol {v} (b{int(b[v])})  coupe {z}  ratio {norm[v, z]:.2f}\n")
print("PNG écrits dans", qc, "| dropouts suspects :", len(suspect[0]))
