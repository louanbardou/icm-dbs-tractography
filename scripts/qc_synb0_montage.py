#!/usr/bin/env python3
"""Porte 1 de l'étape 3B : QC de Synb0-DISCO + topup. Usage : python qc_synb0_montage.py <dossier 03b_synb0> <dossier qc>"""
import sys, os
import numpy as np
import nibabel as nib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

D, Q = sys.argv[1], sys.argv[2]
os.makedirs(Q, exist_ok=True)
load = lambda p: nib.load(os.path.join(D, p)).get_fdata()

b0_d = load("INPUTS/b0.nii.gz")
b0_u = load("OUTPUTS/b0_u.nii.gz")
corr = load("OUTPUTS/b0_all_topup.nii.gz")          # vol 0 = b0 corrigé, vol 1 = synthétique corrigé
b0_c = corr[..., 0]
t1_d = load("qc_tmp/b0_dist_in_T1.nii.gz")          # b0 distordu dans la grille T1
t1_c = load("qc_tmp/b0_corr_in_T1.nii.gz")          # b0 corrigé dans la grille T1
T1 = load("INPUTS/T1.nii.gz")
T1m = load("qc_tmp/T1_brain_mask.nii.gz")        # masque cerveau du T1 (bet), pour le contour


def sl(v, plane, frac):
    n = v.shape["xyz".index(plane)]
    i = int(frac * (n - 1))
    s = {"x": lambda: v[i], "y": lambda: v[:, i], "z": lambda: v[:, :, i]}[plane]()
    return np.rot90(s)


def show(ax, v, plane, frac, title=None, cmap="gray"):
    s = sl(v, plane, frac)
    ax.imshow(s, cmap=cmap, vmin=np.percentile(v[v > 0], 1) if (v > 0).any() else 0,
              vmax=np.percentile(v, 99.5))
    ax.axis("off")
    if title:
        ax.set_title(title, fontsize=9)


# 1. distordu / synthétique / corrigé / T1, 3 plans
fig, axes = plt.subplots(3, 4, figsize=(14, 10))
for r, (plane, frac) in enumerate([("z", 0.45), ("y", 0.5), ("x", 0.5)]):
    show(axes[r, 0], b0_d, plane, frac, "b0 distordu (entrée)" if r == 0 else None)
    show(axes[r, 1], b0_u, plane, frac, "b0 synthétique Synb0" if r == 0 else None)
    show(axes[r, 2], b0_c, plane, frac, "b0 après topup" if r == 0 else None)
    show(axes[r, 3], T1, plane, frac, "T1 (référence)" if r == 0 else None)
fig.suptitle("01 — b0 distordu / synthétique / corrigé / T1 (le synthétique doit avoir la forme du T1)")
fig.tight_layout(); fig.savefig(f"{Q}/01_b0_distordu_synthetique_corrige_T1.png", dpi=110); plt.close(fig)

# 2. contours du T1 (isocontour du masque cerveau T1) sur b0 avant / après, grille T1
fig, axes = plt.subplots(2, 3, figsize=(14, 9))
for c, (plane, frac) in enumerate([("z", 0.45), ("y", 0.45), ("x", 0.5)]):
    for r, (vol, name) in enumerate([(t1_d, "avant topup"), (t1_c, "après topup")]):
        ax = axes[r, c]
        show(ax, vol, plane, frac, f"{name} — {plane}")
        ax.contour(sl(T1m, plane, frac), levels=[0.5], colors="r", linewidths=0.8)
fig.suptitle("02 — contour du masque cerveau T1 (rouge) sur le b0, avant (haut) / après (bas) correction. Regarder frontal et tronc")
fig.tight_layout(); fig.savefig(f"{Q}/02_contour_T1_avant_apres.png", dpi=110); plt.close(fig)

# 3. différence avant / après topup
diff = b0_c - b0_d
fig, axes = plt.subplots(1, 3, figsize=(14, 5))
for ax, (plane, frac) in zip(axes, [("z", 0.45), ("y", 0.5), ("x", 0.5)]):
    s = sl(diff, plane, frac); m = np.percentile(np.abs(diff), 99)
    ax.imshow(s, cmap="RdBu_r", vmin=-m, vmax=m); ax.axis("off"); ax.set_title(plane)
fig.suptitle("03 — b0 corrigé moins b0 distordu (les différences doivent suivre les bords frontaux / tronc)")
fig.tight_layout(); fig.savefig(f"{Q}/03_difference_avant_apres.png", dpi=110); plt.close(fig)

# 4. champ de distorsion (Hz), si disponible
fp = os.path.join(D, "qc_tmp/field_hz.nii.gz")
if os.path.exists(fp):
    f = nib.load(fp).get_fdata()
    mask = b0_d > np.percentile(b0_d, 40)
    vals = f[mask]
    fig, axes = plt.subplots(1, 4, figsize=(16, 4.5))
    for ax, (plane, frac) in zip(axes[:3], [("z", 0.45), ("y", 0.5), ("x", 0.5)]):
        m = np.percentile(np.abs(vals), 99)
        im = ax.imshow(sl(f, plane, frac), cmap="RdBu_r", vmin=-m, vmax=m); ax.axis("off"); ax.set_title(plane)
    fig.colorbar(im, ax=axes[:3], label="Hz", shrink=0.8)
    axes[3].hist(vals, bins=80); axes[3].set_title("histogramme dans le cerveau (Hz)")
    pe_mm = 1.75
    fig.suptitle("04 — champ de distorsion (Hz). Déplacement (voxels) = Hz × 0.0202 s, ×1.75 mm = mm ; "
                 f"médian {np.median(vals):.1f} Hz, |p99| {np.percentile(np.abs(vals), 99):.1f} Hz")
    fig.savefig(f"{Q}/04_champ_distorsion_Hz.png", dpi=110, bbox_inches="tight"); plt.close(fig)
    print(f"champ : médian {np.median(vals):.2f} Hz, p1 {np.percentile(vals, 1):.1f}, p99 {np.percentile(vals, 99):.1f}, "
          f"|max| {np.abs(vals).max():.1f} Hz -> {np.abs(vals).max() * 0.0202278:.2f} voxels = {np.abs(vals).max() * 0.0202278 * 1.75:.1f} mm")
else:
    print("champ Hz non disponible (field_hz.nii.gz absent)")
print("QC écrit dans", Q)
