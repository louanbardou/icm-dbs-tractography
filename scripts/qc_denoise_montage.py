#!/usr/bin/env python
"""QC étape 2 : brut / débruité / résidu / sigma, et avant-après Gibbs sur le b0.
Usage : python qc_denoise_montage.py raw.mif den.mif den_unr.mif residual.mif sigma.mif qc_dir"""
import sys, os, subprocess, tempfile
import numpy as np, nibabel as nib
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

raw, den, unr, res, sig, qc = sys.argv[1:7]; os.makedirs(qc, exist_ok=True); tmp = tempfile.mkdtemp()
def load(mif, vol=None):
    out = os.path.join(tmp, os.path.basename(mif) + ".nii.gz")
    cmd = ["mrconvert", mif, out, "-quiet", "-force"] + (["-coord", "3", str(vol)] if vol is not None else [])
    subprocess.run(cmd, check=True); im = nib.load(out); return np.squeeze(np.asarray(im.dataobj, dtype=np.float32)), im.header.get_zooms()[:3]
# volumes représentatifs : b0 (0), un b1000 (5), un b2000 (45)
vols = [(0, "b0"), (5, "b1000 #5"), (45, "b2000 #45")]
fig, ax = plt.subplots(3, 4, figsize=(16, 12))
for r, (v, name) in enumerate(vols):
    R, z = load(raw, v); D, _ = load(den, v); E, _ = load(res, v)
    Z = R.shape[2] // 2; vmax = np.percentile(R[:, :, Z], 99)
    for c, (img, title) in enumerate([(R, "brut"), (D, "débruité"), (E, "résidu (brut − débruité)")]):
        a = ax[r, c]; a.imshow(img[:, :, Z].T, cmap="gray", origin="lower", vmin=(-vmax * .15 if c == 2 else 0), vmax=(vmax * .15 if c == 2 else vmax), aspect=z[1] / z[0])
        a.set_title(f"{name} — {title}"); a.set_xticks([]); a.set_yticks([])
    S, _ = load(sig); a = ax[r, 3]; im = a.imshow(S[:, :, Z].T, cmap="viridis", origin="lower", aspect=z[1] / z[0]); a.set_title("sigma (carte de bruit estimée)"); a.set_xticks([]); a.set_yticks([]); plt.colorbar(im, ax=a, fraction=.046)
fig.suptitle("MP-PCA — le résidu doit ressembler à de la neige uniforme : AUCUN contour de cerveau, de ventricule ou de faisceau visible", fontsize=12); fig.tight_layout()
fig.savefig(os.path.join(qc, "01_denoise_brut_debruite_residu.png"), dpi=100); plt.close(fig)

# Gibbs : b0 avant/après, zoom sur les ventricules
D0, z = load(den, 0); U0, _ = load(unr, 0); Z = D0.shape[2] // 2; X, Y = D0.shape[:2]
x0, x1, y0, y1 = int(X * .3), int(X * .7), int(Y * .3), int(Y * .7)
fig, ax = plt.subplots(1, 3, figsize=(16, 6)); vmax = np.percentile(D0[:, :, Z], 99.5)
ax[0].imshow(D0[x0:x1, y0:y1, Z].T, cmap="gray", origin="lower", vmax=vmax, aspect=z[1] / z[0], interpolation="nearest"); ax[0].set_title("b0 débruité, AVANT mrdegibbs (zoom ventricules)")
ax[1].imshow(U0[x0:x1, y0:y1, Z].T, cmap="gray", origin="lower", vmax=vmax, aspect=z[1] / z[0], interpolation="nearest"); ax[1].set_title("APRÈS mrdegibbs")
d = (D0 - U0)[x0:x1, y0:y1, Z].T; ax[2].imshow(d, cmap="RdBu_r", origin="lower", vmin=-vmax * .1, vmax=vmax * .1, aspect=z[1] / z[0], interpolation="nearest"); ax[2].set_title("différence — doit être des ondulations fines le long des bords nets")
for a in ax: a.set_xticks([]); a.set_yticks([])
fig.suptitle("Anneaux de Gibbs : chercher des lignes parallèles au bord des ventricules sur 'avant', atténuées sur 'après'"); fig.tight_layout()
fig.savefig(os.path.join(qc, "02_gibbs_avant_apres.png"), dpi=110); plt.close(fig)

# profil 1D à travers un ventricule
mid = D0[x0:x1, y0:y1, Z]; cy = mid.shape[1] // 2
fig, ax = plt.subplots(figsize=(10, 4)); ax.plot(D0[x0:x1, y0 + cy, Z], label="avant"); ax.plot(U0[x0:x1, y0 + cy, Z], label="après"); ax.legend(); ax.set_title("Profil d'intensité gauche-droite à travers les ventricules — les rebonds près des marches doivent diminuer"); ax.set_xlabel("voxel x"); fig.tight_layout()
fig.savefig(os.path.join(qc, "03_gibbs_profil.png"), dpi=110); plt.close(fig)
S, _ = load(sig); print(f"sigma médian dans le cerveau : {np.nanmedian(S[S > 0]):.1f}")
