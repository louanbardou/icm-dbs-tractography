function wp2_diag_vta_reco_auteurs
% WP2 : simulation du VTA sur NOTRE reconstruction, avec le protocole de stimulation des auteurs (month1_par : contact 4, 1,5 V droite / 1,7 V gauche).
% Modèle identique : 'SimBio/FieldTrip (see Horn 2017)' = ea_genvat_horn, seuil E-field = préférence Lead-DBS par défaut.
addpath('/Users/louan/opt/spm12'); addpath('/Users/louan/opt/leaddbs'); ea_setpath; ea_checkspm;
sd='/Users/louan/Folder/ICM/wp2_leaddbs/diag_vta_reco_auteurs/derivatives/leaddbs/sub-DBS01';
options=ea_getptopts(sd); u=load(options.subj.uiprefs); options.elmodel=u.elmodel; options=ea_resolve_elspec(options);
options.native=1; options.orignative=1; options.atlasset='DISTAL Minimal (Ewert 2017)'; options.usediffusion=0; options.patientname='sub-DBS01';
A=load('/Users/louan/Folder/ICM/data/bids/derivatives/leaddbs/sub-DBS01/stimulations/native/month1_par/sub-DBS01_desc-stimparameters.mat'); S=A.S;
fprintf('seuil E-field (V/mm) : %g | gm : %s | atlas : %d\n', options.prefs.machine.vatsettings.horn_ethresh, options.prefs.vat.gm, options.prefs.machine.vatsettings.horn_useatlas);
for side=1:2
    try
        [~,vol]=ea_genvat_horn([],S,side,options,'month1_par'); fprintf('== side %d : volume VTA = %.2f mm3\n',side,vol);
    catch ME
        fprintf('== side %d ERREUR : %s\n',side,ME.message); disp(getReport(ME,'extended','hyperlinks','off'));
    end
end
