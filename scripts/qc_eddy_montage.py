#!/usr/bin/env python
"""QC étape 3 : mouvement par volume, outliers eddy, avant/après sur un b1000 et un b2000.
Usage : python qc_eddy_montage.py in.mif preproc.mif scratch_dir qc_dir"""
import sys, os, subprocess, tempfile, glob
import numpy as np, nibabel as nib
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
inp, pre, scratch, qc = sys.argv[1:5]; os.makedirs(qc, exist_ok=True); tmp = tempfile.mkdtemp()
def load(mif, vol=None):
    out = os.path.join(tmp, os.path.basename(mif) + ".nii.gz")
    subprocess.run(["mrconvert", mif, out, "-quiet", "-force"] + (["-coord", "3", str(vol)] if vol is not None else []), check=True)
    im = nib.load(out); return np.squeeze(np.asarray(im.dataobj, dtype=np.float32)), im.header.get_zooms()[:3]
# 1) mouvement : eddy_movement_rms (col 0 = RMS vs premier volume, col 1 = RMS vs volume précédent)
mv = glob.glob(os.path.join(scratch, "*eddy_movement_rms"))
fig, ax = plt.subplots(2, 1, figsize=(12, 7))
if mv:
    m = np.loadtxt(mv[0]); ax[0].plot(m[:, 0], label="déplacement absolu (vs volume 0)"); ax[0].plot(m[:, 1], label="déplacement relatif (vs volume précédent)")
    ax[0].axhline(1.0, ls="--", c="gray"); ax[0].axhline(2.0, ls="--", c="red"); ax[0].set_ylabel("mm"); ax[0].legend(); ax[0].set_title("Mouvement estimé par eddy — gris = 1 mm, rouge = 2 mm (seuil d'alerte)")
    np.savetxt(os.path.join(qc, "mouvement_rms.txt"), m, fmt="%.3f", header="abs_rms_mm rel_rms_mm")
# 2) outliers par coupe
ol = glob.glob(os.path.join(scratch, "*eddy_outlier_map"))
if ol:
    o = np.loadtxt(ol[0], skiprows=1); im = ax[1].imshow(o.T, aspect="auto", cmap="Reds", origin="lower", interpolation="nearest")
    ax[1].set_xlabel("volume"); ax[1].set_ylabel("coupe z"); pct = 100 * o.sum() / o.size
    ax[1].set_title(f"Coupes remplacées par --repol : {int(o.sum())} sur {o.size} ({pct:.2f} %) — attendu < 5 %")
    with open(os.path.join(qc, "outliers.txt"), "w") as f: f.write(f"{int(o.sum())} coupes outliers sur {o.size} ({pct:.2f} %)\n"); f.write("volumes avec >= 3 coupes remplacées : " + ", ".join(str(i) for i in np.where(o.sum(1) >= 3)[0]) + "\n")
fig.tight_layout(); fig.savefig(os.path.join(qc, "01_mouvement_outliers.png"), dpi=110); plt.close(fig)
# 3) avant / après sur un b1000 et un b2000, axial + sagittal
fig, ax = plt.subplots(2, 4, figsize=(18, 9))
for r, (v, name) in enumerate([(5, "b1000 #5"), (45, "b2000 #45")]):
    A, z = load(inp, v); B, _ = load(pre, v); Z = A.shape[2] // 2; X = A.shape[0] // 2; vmax = np.percentile(A, 99.5)
    ax[r, 0].imshow(A[:, :, Z].T, cmap="gray", origin="lower", vmax=vmax, aspect=z[1] / z[0]); ax[r, 0].set_title(f"{name} avant — axial")
    ax[r, 1].imshow(B[:, :, Z].T, cmap="gray", origin="lower", vmax=vmax, aspect=z[1] / z[0]); ax[r, 1].set_title("après eddy — axial")
    ax[r, 2].imshow(A[X].T, cmap="gray", origin="lower", vmax=vmax, aspect=z[2] / z[1]); ax[r, 2].set_title("avant — sagittal")
    ax[r, 3].imshow(B[X].T, cmap="gray", origin="lower", vmax=vmax, aspect=z[2] / z[1]); ax[r, 3].set_title("après — sagittal")
for a in ax.flat: a.set_xticks([]); a.set_yticks([])
fig.suptitle("Avant / après eddy — chercher : contours plus nets, pas de nouvelle déformation, pas d'étirement en frontal (non corrigé ici)"); fig.tight_layout()
fig.savefig(os.path.join(qc, "02_avant_apres_eddy.png"), dpi=100); plt.close(fig)
# 4) écart-type temporel du shell b1000 avant/après : le mouvement non corrigé crée des bords brillants
A, z = load(inp); B, _ = load(pre); bv = np.loadtxt(os.path.join(scratch, "bvals")) if os.path.exists(os.path.join(scratch, "bvals")) else None
if bv is not None:
    idx = np.isclose(bv, 1000, atol=50); Z = A.shape[2] // 2
    sa, sb = A[..., idx].std(-1), B[..., idx].std(-1); vmax = np.percentile(sa, 99)
    fig, ax = plt.subplots(1, 2, figsize=(11, 5))
    ax[0].imshow(sa[:, :, Z].T, cmap="hot", origin="lower", vmax=vmax, aspect=z[1] / z[0]); ax[0].set_title("écart-type temporel b1000 — AVANT")
    ax[1].imshow(sb[:, :, Z].T, cmap="hot", origin="lower", vmax=vmax, aspect=z[1] / z[0]); ax[1].set_title("APRÈS eddy — les bords brillants (mouvement) doivent s'atténuer")
    for a in ax: a.set_xticks([]); a.set_yticks([])
    fig.tight_layout(); fig.savefig(os.path.join(qc, "03_std_temporel_avant_apres.png"), dpi=110); plt.close(fig)
print("QC écrit dans", qc)
