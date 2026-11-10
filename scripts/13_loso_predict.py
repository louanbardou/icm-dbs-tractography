#!/usr/bin/env python3
"""Prédiction thérapeutique (réponse UPDRS III) à partir des arêtes du VTA, validation LEAVE-ONE-PATIENT-OUT (pas de fuite entre hémisphères d'un même patient).
Même modèle que Presidio (StandardScaler + régression logistique L1), mais évalué proprement ; plus une régression continue (ridge) sur l'amélioration en %.
Avec ~10 patients, résultat exploratoire : AUC avec test de permutation, pas une preuve."""
import numpy as np, os, json, warnings; warnings.filterwarnings('ignore')
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.metrics import roc_auc_score
from scipy.stats import spearmanr
ICM = os.environ.get('ICM', '/Users/louan/Folder/ICM'); D = np.load(f'{ICM}/derivatives/prediction/master.npz', allow_pickle=True)
key = os.environ.get('FEAT', 'X'); X = np.log1p(D[key]); y = D['y']; imp = D['improvement']; g = D['groups']
keep = (D[key] > 0).sum(0) >= 2; X = X[:, keep]; print('échantillons', len(y), 'patients', len(set(g)), 'arêtes retenues (présentes dans >=2 VTA):', X.shape[1], '| y=1:', y.sum())
def loso(make, target, proba):
    out = np.zeros(len(y)); 
    for tr, te in LeaveOneGroupOut().split(X, y, g):
        m = make(); m.fit(X[tr], target[tr]); out[te] = m.predict_proba(X[te])[:, 1] if proba else m.predict(X[te])
    return out
mk_log = lambda: make_pipeline(StandardScaler(), LogisticRegression(penalty='l1', solver='liblinear', C=float(os.environ.get('C', 1)), class_weight='balanced', max_iter=2000))
mk_rdg = lambda: make_pipeline(StandardScaler(), Ridge(alpha=1e4))
res = {}
if 0 < y.sum() < len(y) and len(set(y)) == 2:
    p = loso(mk_log, y, True); auc = roc_auc_score(y, p)
    rng = np.random.default_rng(0); perm = []
    for _ in range(int(os.environ.get('NPERM', 200))):
        ys = y.copy()
        for gg in set(g): pass
        # permutation au niveau PATIENT (les 2 hémisphères gardent le même label)
        subs = np.array(sorted(set(g))); lab = np.array([y[g == s][0] for s in subs]); lp = rng.permutation(lab); ys = np.array([lp[list(subs).index(s)] for s in g])
        pp = np.zeros(len(y))
        for tr, te in LeaveOneGroupOut().split(X, ys, g):
            if len(set(ys[tr])) < 2: pp[te] = 0.5; continue
            m = mk_log(); m.fit(X[tr], ys[tr]); pp[te] = m.predict_proba(X[te])[:, 1]
        perm.append(roc_auc_score(ys, pp))
    res['logreg_L1_AUC_LOPO'] = float(auc); res['perm_p'] = float((np.sum(np.array(perm) >= auc) + 1) / (len(perm) + 1))
r = loso(mk_rdg, imp, False); rho, pv = spearmanr(r, imp); res['ridge_spearman_LOPO'] = float(rho); res['ridge_spearman_p'] = float(pv)
print(json.dumps(res, indent=1)); json.dump(res, open(f'{ICM}/derivatives/prediction/loso_results_{key}.json', 'w'), indent=1)
