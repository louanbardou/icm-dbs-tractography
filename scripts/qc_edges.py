#!/usr/bin/env python3
"""Figures for the edge connectome and the prediction labels.
  qc/edges/edge_connectome.png          whole-brain vs VTA matrix of one subject (log scale)
  qc/prediction/improvement_per_patient.png   UPDRS III improvement used as label, with the median cut
Usage: python scripts/qc_edges.py [sub-DBS05]"""
import numpy as np, os, sys, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
ICM = os.environ.get('ICM', os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sub = sys.argv[1] if len(sys.argv) > 1 else 'sub-DBS05'
E = f'{ICM}/derivatives/cohort/{sub}/11_edges'; N = 388; iu = np.triu_indices(N, 1)
def mat(f):
    v = np.loadtxt(f, delimiter=','); M = np.zeros((N, N)); M[iu] = v; return M + M.T
W, L, R = mat(f'{E}/whole_upper_tri_sift2.csv'), mat(f'{E}/vta_L_upper_tri_sift2.csv'), mat(f'{E}/vta_R_upper_tri_sift2.csv')
groups = [(0, 180, 'Glasser L'), (180, 360, 'Glasser R'), (360, 386, 'Tian (subcortex)'), (386, 388, 'STN')]
fig, ax = plt.subplots(1, 3, figsize=(17, 5.6))
for a, M, t in zip(ax, (W, L, R), ('whole brain', 'streamlines through the left VTA', 'streamlines through the right VTA')):
    im = a.imshow(np.log10(M + 1e-3 * 0 + 1), cmap='magma', interpolation='nearest'); a.set_title(f'{t}\n{int((M[iu] > 0).sum()):,} non-zero edges', fontsize=13)
    for s, e, _ in groups[:3]: a.axhline(e - .5, color='w', lw=.4); a.axvline(e - .5, color='w', lw=.4)
    a.set_xticks([(s + e) / 2 for s, e, _ in groups[:3]]); a.set_xticklabels(['Glasser L', 'Glasser R', 'Tian'], fontsize=10); a.set_yticks([])
    plt.colorbar(im, ax=a, fraction=.046, label='log10(1 + SIFT2 weight)')
fig.suptitle(f'{sub}: edge connectome, 388 nodes', fontsize=15); fig.tight_layout(); os.makedirs(f'{ICM}/qc/edges', exist_ok=True); fig.savefig(f'{ICM}/qc/edges/edge_connectome.png', dpi=110)
import pandas as pd
m = pd.read_csv(f'{ICM}/derivatives/prediction/master_meta.tsv', sep='\t').drop_duplicates('sub'); thr = m.improvement.median()
fig, a = plt.subplots(figsize=(9, 4.6)); m = m.sort_values('improvement')
a.bar(m['sub'].str.replace('sub-', ''), m.improvement, color=np.where(m.improvement >= thr, '#1f77b4', '#ff7f0e')); a.axhline(thr, color='k', ls='--', lw=1); a.text(0, thr + 1.5, f'median cut = {thr:.0f}%', fontsize=11)
a.set_ylabel('UPDRS III improvement at 1 month (%)'); a.set_title('Label used for the prediction (blue = responder, orange = not)', fontsize=12); plt.xticks(rotation=45); fig.tight_layout()
os.makedirs(f'{ICM}/qc/prediction', exist_ok=True); fig.savefig(f'{ICM}/qc/prediction/improvement_per_patient.png', dpi=120)
