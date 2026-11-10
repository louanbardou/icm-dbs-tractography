function wp2_compare_contacts
% WP2 : distance contact par contact entre NOTRE reconstruction (PaCER) et celle des auteurs (PaCER + correction manuelle).
% Critère du plan : < 1 mm attendu. Sortie : wp2_leaddbs/compare/contacts_distances.csv + résumé affiché.
ours  ='/Users/louan/Folder/ICM/wp2_leaddbs/derivatives/leaddbs/sub-DBS01/reconstruction/sub-DBS01_desc-reconstruction.mat';
theirs='/Users/louan/Folder/ICM/data/bids/derivatives/leaddbs/sub-DBS01/reconstruction/sub-DBS01_desc-reconstruction.mat';
A=load(ours); B=load(theirs); out='/Users/louan/Folder/ICM/wp2_leaddbs/compare/contacts_distances.csv';
fid=fopen(out,'w'); fprintf(fid,'space,side,contact,ours_x,ours_y,ours_z,ref_x,ref_y,ref_z,dist_mm\n');
sn={'R','L'}; 
for sp={'native','mni'}
  for s=1:2
    a=A.reco.(sp{1}).coords_mm{s}; b=B.reco.(sp{1}).coords_mm{s};
    d=sqrt(sum((a-b).^2,2));
    for c=1:size(a,1), fprintf(fid,'%s,%s,%d,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f\n',sp{1},sn{s},c,a(c,:),b(c,:),d(c)); end
    % angle entre les axes d'électrode (contact 1 -> dernier)
    va=a(end,:)-a(1,:); vb=b(end,:)-b(1,:); ang=acosd(dot(va,vb)/(norm(va)*norm(vb)));
    fprintf('%-6s %s : distances (mm) %s | moy %.2f max %.2f | angle des axes %.2f deg\n',sp{1},sn{s},mat2str(d',3),mean(d),max(d),ang);
  end
end
fclose(fid);
fprintf('manually_corrected (auteurs): %d | (nous): %d\n',B.reco.props(1).manually_corrected,A.reco.props(1).manually_corrected);
