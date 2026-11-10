function wp2_diag_traj_fix
% DIAGNOSTIC uniquement (copie wp2_leaddbs/diag_vta_traj_corrigee) : remplace la trajectoire native/scrf (qui s'éloigne de 60 mm à l'opposé du contact 4)
% par une droite de 50 points de -5 à +15 mm le long de l'axe contact1->contact4, comme chez les auteurs. N'altère PAS wp2_leaddbs/derivatives.
f='/Users/louan/Folder/ICM/wp2_leaddbs/diag_vta_traj_corrigee/derivatives/leaddbs/sub-DBS01/reconstruction/sub-DBS01_desc-reconstruction.mat';
r=load(f); reco=r.reco;
for sp={'native','scrf'}
  for s=1:2
    c=reco.(sp{1}).coords_mm{s}; ax=(c(4,:)-c(1,:))/norm(c(4,:)-c(1,:)); t=old(reco.(sp{1}).trajectory{s},c,ax);
    assert(t<0,'trajectoire déjà dans le bon sens');
    reco.(sp{1}).trajectory{s}=c(1,:)+linspace(-5,15,50)'*ax;
  end
end
save(f,'reco'); disp('trajectoire corrigée (copie diagnostic)');
end
function p=old(t,c,ax), p=(t(end,:)-c(1,:))*ax'; end
