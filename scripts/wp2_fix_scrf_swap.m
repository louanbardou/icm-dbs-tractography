function wp2_fix_scrf_swap
% Correction documentée : dans NOTRE reconstruction, reco.scrf (coordonnées corrigées du brainshift) a les côtés 1 et 2 permutés
% (scrf{1} = native{2} à ~0,2 mm près ; native, mni et les dérivés des auteurs sont corrects). On échange les côtés dans scrf.
% Sauvegarde de l'original : wp2_leaddbs/logs/reconstruction_AVANT_swap_scrf.mat
f='/Users/louan/Folder/ICM/wp2_leaddbs/derivatives/leaddbs/sub-DBS01/reconstruction/sub-DBS01_desc-reconstruction.mat';
r=load(f); reco=r.reco;
% garde-fou : on ne corrige que si la permutation est bien observée (x du contact 4 de scrf{1} et de native{1} de signes opposés)
x1s=reco.scrf.coords_mm{1}(4,1); x1n=reco.native.coords_mm{1}(4,1);
if sign(x1s)==sign(x1n), error('Pas de permutation observée, rien modifié.'); end
reco.scrf.coords_mm=reco.scrf.coords_mm([2 1]); reco.scrf.trajectory=reco.scrf.trajectory([2 1]); reco.scrf.markers=reco.scrf.markers([2 1]);
for k=1:2, d=norm(reco.scrf.coords_mm{k}(4,:)-reco.native.coords_mm{k}(4,:)); fprintf('side %d : décalage brainshift scrf-native au contact 4 = %.2f mm\n',k,d); assert(d<2); end
save(f,'reco'); disp('scrf corrigé et sauvegardé.');
