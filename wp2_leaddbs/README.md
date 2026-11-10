# WP2 — reconstruction Lead-DBS refaite par nous, comparée aux auteurs
- `rawdata/` : images brutes copiées depuis `../data/bids/sub-DBS01` (T1 -> acq-iso_T1w ; TSE transversal -> acq-ax_T2w ; CT 1 mois -> ses-postop_CT). Rien des dérivés des auteurs.
- `derivatives/leaddbs/sub-DBS01/` : sorties de NOTRE run Lead-DBS 3.2.1 (MATLAB R2025b, /Users/louan/opt/leaddbs).
- Vérité de comparaison : `../data/bids/derivatives/leaddbs/sub-DBS01/` (jamais modifiée).
- `compare/` : scripts et résultats de comparaison ; `logs/` : journaux MATLAB ; QC visuel dans `../qc/WP2_leaddbs/`.
- Lancement : `scripts/wp2_run.sh pre|post`.
