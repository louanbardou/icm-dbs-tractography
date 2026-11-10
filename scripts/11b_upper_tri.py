import numpy as np, sys, os
O, sub = sys.argv[1], sys.argv[2]
for p in ['whole', 'vta_L', 'vta_R']:
    for k in ['sift2', 'count']:
        M = np.loadtxt(f'{O}/{p}_{k}.csv', delimiter=' ' if ' ' in open(f'{O}/{p}_{k}.csv').readline() else ',')
        iu = np.triu_indices(M.shape[0], 1)
        np.savetxt(f'{O}/{p}_upper_tri_{k}.csv', M[iu][None, :], delimiter=',', fmt='%.6g')
        print(sub, p, k, M.shape, 'arêtes non nulles', int((M[iu] > 0).sum()), 'somme', round(float(M[iu].sum()), 2))
