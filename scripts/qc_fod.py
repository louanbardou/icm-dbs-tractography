#!/usr/bin/env python
"""QC étape 6 : voxels de réponse, fonctions de réponse, fractions de volume, pics de FOD. Usage : python qc_fod.py dossier_06 dossier_05 dossier_qc"""
import sys, os, subprocess, tempfile, numpy as np, nibabel as nib
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
D, I, Q = sys.argv[1:4]; os.makedirs(Q, exist_ok=True); tmp = tempfile.mkdtemp()
def nii(mif, *extra):
    o = os.path.join(tmp, os.path.basename(mif) + ".nii.gz"); subprocess.run(["mrconvert", mif, o, "-force", "-quiet", *extra], check=True)
    return np.asarray(nib.load(o).dataobj, np.float32)
sl = lambda v, p, i: np.rot90({"x": lambda: v[i], "y": lambda: v[:, i], "z": lambda: v[:, :, i]}[p]())
b0 = nii(os.path.join(I, "dwi_T1.mif"), "-coord", "3", "0"); b0 = b0[..., 0] if b0.ndim == 4 else b0
mask = nii(os.path.join(I, "mask_T1.mif")) > 0.5
vox = nii(os.path.join(D, "voxels.mif"))   # 4D : 1=CSF, 2=GM, 3=WM selon version -> on lit les 3 volumes
if vox.ndim == 3: vox = vox[..., None]
# 1. voxels sélectionnés pour chaque tissu
fig, ax = plt.subplots(1, 3, figsize=(16, 5.5)); z = int(np.argwhere(mask)[:, 2].mean() + 3)
for a, (k, name, col) in zip(ax, [(0, "CSF", "Blues"), (1, "GM", "Greens"), (2, "WM", "Reds")]):
    a.imshow(sl(b0, "z", z), cmap="gray", vmax=np.percentile(b0[mask], 99)); m = sl(vox[..., min(k, vox.shape[3] - 1)], "z", z)
    a.imshow(np.ma.masked_where(m < 0.5, m), cmap=col, alpha=0.9); a.axis("off"); a.set_title(f"voxels {name} (n = {int((vox[..., min(k, vox.shape[3]-1)] > 0.5).sum())})")
fig.suptitle("01 — voxels choisis par dhollander : CSF dans les ventricules, GM dans le cortex, WM pur dans la substance blanche (pas aux interfaces)")
fig.tight_layout(); fig.savefig(os.path.join(Q, "01_voxels_reponse.png"), dpi=100); plt.close(fig)
# 2. fonctions de réponse : coefficient l=0 (et l=2,4...) par shell
fig, ax = plt.subplots(1, 3, figsize=(15, 4))
for a, t in zip(ax, ["wm", "gm", "csf"]):
    r = np.loadtxt(os.path.join(D, f"{t}.txt"), ndmin=2)
    for l in range(r.shape[1]): a.plot(r[:, l], "o-", label=f"l={2*l}")
    a.set_title(f"réponse {t.upper()} ({r.shape[0]} shells, lignes = b0 / b1000 / b2000)"); a.set_xticks(range(r.shape[0])); a.set_xticklabels(["b0", "b1000", "b2000"][:r.shape[0]]); a.legend(fontsize=7)
fig.suptitle("02 — fonctions de réponse. WM : l=0 qui décroît avec b, l=2 fort (forme de galette/aiguille). GM et CSF : l=0 seul, CSF qui chute le plus vite")
fig.tight_layout(); fig.savefig(os.path.join(Q, "02_fonctions_reponse.png"), dpi=100); plt.close(fig)
# 3. fractions de volume (l=0 de chaque tissu) en RGB : rouge = CSF, vert = GM, bleu = WM
c = [nii(os.path.join(D, f"{t}_norm.mif"), "-coord", "3", "0") for t in ("csf", "gm", "wmfod")]
c = [x[..., 0] if x.ndim == 4 else x for x in c]; rgb = np.stack([np.clip(x / (np.percentile(x[mask], 99.5) + 1e-9), 0, 1) for x in c], -1)
fig, ax = plt.subplots(1, 3, figsize=(16, 6))
for a, (p, i) in zip(ax, [("z", z), ("y", b0.shape[1] // 2), ("x", b0.shape[0] // 2)]):
    a.imshow(sl(rgb * mask[..., None], p, i)); a.axis("off"); a.set_title(p)
fig.suptitle("03 — fractions de volume : rouge = CSF (ventricules), vert = GM (cortex, noyaux gris), bleu = WM. Les noyaux gris profonds doivent être verts, la capsule interne bleue")
fig.tight_layout(); fig.savefig(os.path.join(Q, "03_fractions_volume_RGB.png"), dpi=100); plt.close(fig)
# 4. pics de FOD : nombre de pics et direction principale colorée
pk = np.nan_to_num(nii(os.path.join(D, "peaks.mif")))   # 9 volumes = 3 pics x (x,y,z) ; amplitude = norme
n = np.sum([np.linalg.norm(pk[..., 3*j:3*j+3], axis=-1) > 0 for j in range(3)], 0) * mask
d1 = pk[..., 0:3]; col = np.clip(np.abs(d1) * (np.linalg.norm(d1, axis=-1, keepdims=True) / (np.percentile(np.linalg.norm(d1, axis=-1)[mask], 99) + 1e-9)), 0, 1)
fig, ax = plt.subplots(2, 3, figsize=(16, 10))
for k, (p, i) in enumerate([("z", z), ("y", b0.shape[1] // 2), ("x", b0.shape[0] // 2)]):
    ax[0, k].imshow(sl(col * mask[..., None], p, i)); ax[0, k].axis("off"); ax[0, k].set_title(f"direction du pic principal (couleur × amplitude) — {p}")
    im = ax[1, k].imshow(sl(n, p, i), cmap="viridis", vmin=0, vmax=3); ax[1, k].axis("off"); ax[1, k].set_title(f"nombre de pics (0-3) — {p}")
fig.colorbar(im, ax=ax[1, :], shrink=0.6)
fig.suptitle("04 — pics des FOD : corps calleux rouge / CST bleu ; 1 pic dans le corps calleux, 2-3 pics dans le centre semi-ovale et la couronne rayonnante (croisements)")
fig.savefig(os.path.join(Q, "04_pics_FOD.png"), dpi=100, bbox_inches="tight"); plt.close(fig)
print("QC écrit dans", Q, "| pics : 1 pic %.0f %%, 2 pics %.0f %%, 3 pics %.0f %% des voxels du masque" % tuple(100 * (n[mask] == k).mean() for k in (1, 2, 3)))
