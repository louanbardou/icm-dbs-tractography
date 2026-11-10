#!/usr/bin/env python3
"""Assemble les vecteurs d'arêtes par VTA (triangle supérieur, SIFT2) + labels cliniques -> derivatives/prediction/master.npz
Équivalent de build_master_data_presidio.py. Un échantillon = un VTA (patient x hémisphère).
Label : amélioration de l'UPDRS III à 1 mois, OFF-stim -> stimulation haute fréquence (CH, 130 Hz, réglage clinique), moyenne des 2 évaluateurs.
Attention : les 3 conditions CL/CH/CV (60 Hz / 130 Hz / variable) ont le MÊME VTA ; elles ne donnent donc pas d'échantillons supplémentaires."""
import numpy as np, pandas as pd, os, sys, json
ICM = os.environ.get('ICM', os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); thr = os.environ.get('THR')
def edir(sub):
    for d in (f'{ICM}/derivatives/cohort/{sub}/11_edges', f'{ICM}/derivatives/tracto/11_edges'):
        if sub != 'sub-DBS01' and 'tracto' in d: continue
        if os.path.exists(f'{d}/vta_L_upper_tri_sift2.csv'): return d
d = pd.read_csv(f'{ICM}/data/bids/phenotype/UPDRS_III.tsv', sep='\t'); d['sub'] = 'sub-' + d.iloc[:, 0].astype(str).str.replace('sub-', '')
d['s'] = (d.rater1 + d.rater2) / 2; p = d.pivot_table(index='sub', columns='condition', values='s')
p['improvement'] = (p['1mOFF'] - p['1mCH']) / p['1mOFF'] * 100
rows, X, Xc, skipped = [], [], [], []
for sub in sorted(p.index):
    e = edir(sub); imp = p.loc[sub, 'improvement']; off = p.loc[sub, '1mOFF']
    if e is None: skipped.append((sub, 'pas de connectome (pas de DWI ou pas encore traité)')); continue
    if not np.isfinite(imp) or off < 10: skipped.append((sub, f'label inutilisable (OFF 1 mois={off})')); continue
    for h in 'LR':
        X.append(np.loadtxt(f'{e}/vta_{h}_upper_tri_sift2.csv', delimiter=',')); Xc.append(np.loadtxt(f'{e}/vta_{h}_upper_tri_count.csv', delimiter=','))
        rows.append(dict(sub=sub, hemi=h, improvement=imp, off=off))
meta = pd.DataFrame(rows); thr = float(thr) if thr else float(meta.improvement.median())   # par défaut : médiane (un seuil à 50 % rend presque tous les patients répondeurs)
meta['y'] = (meta.improvement >= thr).astype(int)
os.makedirs(f'{ICM}/derivatives/prediction', exist_ok=True)
np.savez_compressed(f'{ICM}/derivatives/prediction/master.npz', X=np.array(X), Xcount=np.array(Xc), y=meta.y.values, improvement=meta.improvement.values, groups=meta['sub'].values, hemi=meta.hemi.values)
meta.to_csv(f'{ICM}/derivatives/prediction/master_meta.tsv', sep='\t', index=False)
print(meta.to_string()); print('seuil réponse', thr, '% | échantillons', len(meta), '| patients', meta['sub'].nunique(), '| y=1:', int(meta.y.sum()))
print('exclus :', skipped)
