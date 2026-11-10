#!/usr/bin/env python3
"""Télécharge, par FTP en lecture seule (ScienceDB 26302), le STRICT NÉCESSAIRE par patient (pas les ~613 Go du dataset).
Par patient : T1w et DWI pré-op (rawdata) + dérivés Lead-DBS des auteurs : reconstruction, VTA natifs, atlas natif, T1 d'ancrage,
transformation MNI->natif, prefs. Reprise possible (fichiers de même taille ignorés).
Usage : FTP_USER=... FTP_PASS=... python3 scripts/10_download_openDBS.py sub-DBS02 [sub-DBS03 ...]
"""
import ftplib, os, re, sys, time
HOST, PORT = 'ftp.scidb.cn', 2121
DEST = os.environ.get('BIDS', os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'bids'))
USER, PASS = os.environ['FTP_USER'], os.environ['FTP_PASS']

def connect():
    f = ftplib.FTP(); f.connect(HOST, PORT, timeout=120); f.login(USER, PASS); f.set_pasv(True); return f

def listdir(f, p):
    L = []; f.retrlines('LIST ' + p, L.append); out = []
    for l in L:
        t = l.split(None, 8)
        if len(t) == 9: out.append((t[8], t[0][0] == 'd', int(t[4])))
    return out

def walk(f, p):
    for n, d, s in listdir(f, p):
        if d: yield from walk(f, p + '/' + n)
        else: yield p + '/' + n, s

def wanted(path, sub):
    r = path
    if re.search(rf'^/{sub}/ses-preop/anat/{sub}_ses-preop_T1w\.(nii\.gz|json)$', r): return True
    if re.search(rf'^/{sub}/ses-preop/dwi/', r): return True
    d = f'/derivatives/leaddbs/{sub}/'
    if not r.startswith(d): return False
    x = r[len(d):]
    if x.startswith('prefs/') or x.startswith('atlases/'): return True
    if x.startswith('reconstruction/') and x.endswith('.mat'): return True
    if x.startswith('stimulations/native/') and x.endswith(('.nii', '.mat')): return True
    if x.startswith('coregistration/anat/') and 'preop' in x and x.endswith('T1w.nii'): return True
    if x.startswith('coregistration/transformations/'): return True
    if x.startswith('normalization/transformations/') and f'from-MNI152NLin2009bAsym_to-anchorNative' in x: return True
    return False

def get(f, remote, size):
    loc = DEST + remote if not remote.startswith('/derivatives') else DEST + remote
    os.makedirs(os.path.dirname(loc), exist_ok=True)
    if os.path.exists(loc) and os.path.getsize(loc) == size: return 0
    tmp = loc + '.part'
    for k in range(5):
        try:
            with open(tmp, 'wb') as g: f.retrbinary('RETR ' + remote, g.write, blocksize=1 << 20)
            if os.path.getsize(tmp) != size: raise IOError('taille')
            os.replace(tmp, loc); return size
        except Exception as e:
            print('  retry', remote, e, flush=True); time.sleep(5)
            try: f.close()
            except Exception: pass
            f = connect()
    raise SystemExit('échec ' + remote)

for sub in sys.argv[1:]:
    f = connect(); t0 = time.time(); n = tot = 0
    files = [(p, s) for root in (f'/{sub}/ses-preop', f'/derivatives/leaddbs/{sub}') for p, s in walk(f, root) if wanted(p, sub)]
    print(f'{sub}: {len(files)} fichiers, {sum(s for _, s in files) / 1e6:.0f} Mo à vérifier/télécharger', flush=True)
    for p, s in files: tot += get(f, p, s); n += 1
    print(f'{sub}: OK ({tot / 1e6:.0f} Mo téléchargés, {time.time() - t0:.0f} s)', flush=True)
    f.close()
