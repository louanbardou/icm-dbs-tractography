function wp2_run(stage)
% WP2 : pipeline Lead-DBS headless sur ICM/wp2_leaddbs. stage = 'pre' | 'post'.
% Copie de helpers/ea_runProcessing.m (Lead-DBS 3.2.1) avec UNE différence assumée : coregmr = SPM12 (comme les auteurs,
% leur log : "ea_spm_coreg ... SPM12"), au lieu d'ANTs codé en dur. Le reste (ANTs SyN, brainshift 'Coarse', PaCER) est identique.
addpath('/Users/louan/opt/spm12'); addpath('/Users/louan/opt/leaddbs'); ea_setpath;
ea_checkspm;   % déploie les MEX SPM12 pour Apple Silicon (zip fourni par Lead-DBS), comme à l'ouverture de l'interface
dataset='/Users/louan/Folder/ICM/wp2_leaddbs'; pid='DBS01';
sd=fullfile(dataset,'derivatives','leaddbs',['sub-' pid]);
uf=fullfile(sd,'prefs',['sub-' pid '_desc-uiprefs.mat']);
if ~isfile(uf)   % préférences minimales : modèle d'électrode du dataset (PINS L301), 2 côtés, CT postop
    modality=2; sides=[1 2]; elmodel='PINS Medical L301'; save(uf,'modality','sides','elmodel');
end
options = ea_getptopts(sd); options.overwriteapproved=0;
uiprefs=load(options.subj.uiprefs); options.elmodel=uiprefs.elmodel; options=ea_resolve_elspec(options);
fprintf('== wp2_run(%s) %s\n', stage, datestr(now));
subjAnchor = regexprep(options.subj.AnchorModality, '[^\W_]+_', '');
if ismember(subjAnchor, fieldnames(options.bids.spacedef.norm_mapping)), options.primarytemplate = options.bids.spacedef.norm_mapping.(subjAnchor);
else, options.primarytemplate = options.bids.spacedef.misfit_template; end
options.coregmr.method='SPM (Friston 2007)'; options.coregct.method='ANTs (Avants 2008)'; options.normalize.method='ANTs (Avants 2008)';
pp=@(s) ea_cprintf('*Comments','%s\n',s);
if strcmp(stage,'pre')
    f=fieldnames(options.subj.preopAnat);
    for i=1:numel(f)
        a=options.subj.preopAnat.(f{i});
        if ~isfile(a.preproc)
            ea_mkdir(fileparts(a.preproc));
            if strcmp(options.prefs.niiFileExt,'.nii'), copyfile(a.raw,[a.preproc '.gz']); gunzip([a.preproc '.gz']); delete([a.preproc '.gz']);
            else, copyfile(a.raw,a.preproc); end
            ea_anatpreprocess(a.preproc);
            if isfield(options.subj,'postopAnat'), ea_resliceanat(a.preproc); end
        end
    end
    pp('preprocessing preop fini');
    A=options.subj.AnchorModality;
    if ~isfile(options.subj.preopAnat.(A).coreg)
        ea_precoreg(options.subj.preopAnat.(A).preproc, options.primarytemplate, options.subj.preopAnat.(A).coreg, options.subj.coreg.transform.(A));
    end
    ea_coregpreopmr(options); ea_gencheckregfigs(options,'coreg'); pp('coregistration MR fini');
    ea_normalize(options); ea_gencheckregfigs(options,'norm'); pp('normalisation fini');
elseif strcmp(stage,'post')
    f=fieldnames(options.subj.postopAnat);
    for i=1:numel(f)
        a=options.subj.postopAnat.(f{i});
        if ~isfile(a.preproc)
            ea_mkdir(fileparts(a.preproc));
            if strcmp(options.prefs.niiFileExt,'.nii'), copyfile(a.raw,[a.preproc '.gz']); gunzip([a.preproc '.gz']); delete([a.preproc '.gz']);
            else, copyfile(a.raw,a.preproc); end
        end
    end
    if strcmp(options.subj.postopModality,'CT'), ea_coregpostopct(options); else, ea_coregpostopmr(options); end
    ea_gencheckregfigs(options,'coreg'); pp('coregistration postop fini');
    ea_apply_normalization(options); ea_gencheckregfigs(options,'norm'); pp('normalisation postop appliquee');
    options.autobrainshift=1; options.d2.write=0; options.d3.write=0; options.scrf.mask='Coarse';
    ea_subcorticalrefine(options); pp('brainshift fini');
    options.hybridsave=1; options.reconmethod='PaCER (Husch 2017)'; ea_mkdir(options.subj.reconDir);
    [coords_mm,trajectory,markers]=ea_runpacer(options); options.native=1;
    ea_save_reconstruction(coords_mm,trajectory,markers,options.elmodel,0,options); pp('PaCER fini');
end
fprintf('== wp2_run(%s) FIN %s\n', stage, datestr(now));
