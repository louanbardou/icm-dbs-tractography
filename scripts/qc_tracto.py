#!/usr/bin/env python
"""QC étape 8 : TDI sur T1, projections des streamlines, symétrie G/D, streamlines dans le CSF. Usage : python qc_tracto.py dossier_08 dossier_ref dossier_07 dossier_qc"""
import sys, os, subprocess, tempfile, numpy as np, nibabel as nib
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
D, REF, A, Q = sys.argv[1:5]; os.makedirs(Q, exist_ok=True); tmp = tempfile.mkdtemp()
def nii(p):
    o = os.path.join(tmp, os.path.basename(p) + ".nii.gz"); subprocess.run(["mrconvert", p, o, "-quiet", "-force"], check=True); return nib.load(o)
T1i = nib.load(os.path.join(REF, "T1.nii.gz")); T1 = np.asarray(T1i.dataobj, np.float32)
tdi_i = nii(os.path.join(D, "tdi_sift2_1mm.mif")); tdi = np.asarray(tdi_i.dataobj, np.float32)
sl = lambda v, p, i: np.rot90({"x": lambda: v[i], "y": lambda: v[:, i], "z": lambda: v[:, :, i]}[p]())
# TDI est sur une grille 1 mm : on la montre seule sur le fond noir + contour cerveau T1 rééchantillonné
from nibabel.processing import resample_from_to
bm = nib.load(os.path.join(REF, "T1_brain_mask.nii.gz")); bm1 = np.asarray(resample_from_to(bm, tdi_i, order=0).dataobj) > 0
fig, ax = plt.subplots(2, 3, figsize=(17, 11)); sh = np.array(tdi.shape)
lt = np.log1p(tdi / (np.percentile(tdi[tdi > 0], 99) + 1e-9))
for k, (p, i) in enumerate([("z", int(sh[2] * 0.5)), ("y", int(sh[1] * 0.5)), ("x", int(sh[0] * 0.5))]):
    ax[0, k].imshow(sl(lt, p, i), cmap="inferno"); ax[0, k].contour(sl(bm1.astype(float), p, i), [0.5], colors="cyan", linewidths=0.5); ax[0, k].axis("off"); ax[0, k].set_title(f"TDI SIFT2 (log) {p}={i}")
for k, (p, i) in enumerate([("z", int(sh[2] * 0.35)), ("y", int(sh[1] * 0.45)), ("x", int(sh[0] * 0.5) - 25)]):
    ax[1, k].imshow(sl(lt, p, i), cmap="inferno"); ax[1, k].contour(sl(bm1.astype(float), p, i), [0.5], colors="cyan", linewidths=0.5); ax[1, k].axis("off"); ax[1, k].set_title(f"{p}={i}")
fig.suptitle("01 — densité de streamlines pondérée SIFT2 (échelle log) + contour du cerveau (cyan). Le cerveau doit être rempli de substance blanche, sans streamline dans les ventricules ni hors du cerveau")
fig.tight_layout(); fig.savefig(os.path.join(Q, "01_TDI_sift2.png"), dpi=100); plt.close(fig)
# 2. projections de 20k streamlines colorées par direction
tr = nib.streamlines.load(os.path.join(D, "tracks_200k.tck")); S = tr.streamlines; idx = np.arange(0, len(S), max(1, len(S) // 20000))
fig, ax = plt.subplots(1, 3, figsize=(18, 6)); pl = [(0, 1, "axial (x,y)"), (0, 2, "coronal (x,z)"), (1, 2, "sagittal (y,z)")]
for a, (i, j, nm) in zip(ax, pl):
    for s in idx:
        s = S[s]; d = np.abs(np.gradient(s, axis=0)); d = d / (np.linalg.norm(d, axis=1, keepdims=True) + 1e-9)
        a.plot(s[:, i], s[:, j], lw=0.15, color=np.clip(d.mean(0) * 1.8, 0, 1), alpha=0.5)
    a.set_aspect("equal"); a.axis("off"); a.set_title(nm)
fig.suptitle("02 — 20 000 streamlines (sur 200k) colorées par direction (rouge G-D, vert A-P, bleu H-B) : CC rouge, CST bleu, cingulum/arqué vert, symétrie G/D")
fig.tight_layout(); fig.savefig(os.path.join(Q, "02_streamlines_projections.png"), dpi=100); plt.close(fig)
# 3. symétrie gauche/droite de la TDI + streamlines dans le CSF (ACT : doit être ~0)
t5 = nii(os.path.join(A, "5tt_stn.mif")); T5 = np.asarray(t5.dataobj, np.float32)
c = np.array(tdi.shape) // 2; mid = np.argwhere(tdi > 0).mean(0)[0]
left, right = tdi[: int(mid)].sum(), tdi[int(mid):].sum()
csf = np.asarray(resample_from_to(nib.Nifti1Image(T5[..., 3], t5.affine), tdi_i, order=1).dataobj)
frac_csf = float((tdi * (csf > 0.5)).sum() / tdi.sum())
with open(os.path.join(Q, "metriques.txt"), "w") as f:
    f.write(f"TDI SIFT2 : somme gauche/droite du plan x={mid:.0f} : {left:.3g} / {right:.3g} (rapport {left/right:.2f})\nfraction de la TDI pondérée dans des voxels CSF>0,5 : {frac_csf:.4f}\nstreamlines dans tracks_200k : {len(S)}\n")
print(open(os.path.join(Q, "metriques.txt")).read())
