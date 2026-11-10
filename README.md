# icm-dbs-tractography

Small side project where I play with an open deep brain stimulation (DBS) dataset: one patient with electrodes in the subthalamic nucleus (STN), published on ScienceDB (dataset 26302). It comes with raw MRI/CT, diffusion data and the authors' own Lead-DBS results.

## What I'm trying to do

1. **Tractography.** Run a diffusion pipeline with MRtrix3/FSL/ANTs (denoising, eddy/topup with Synb0-DISCO, CSD, anatomically constrained tractography with SIFT2), in the patient's own space so it lines up with the Lead-DBS electrodes. Then pull out DBS-relevant bundles (STN to motor cortex, STN to GPi, etc.). The bundle extraction is not done yet.
2. **Redo the Lead-DBS reconstruction (WP2).** Rerun it headless from the raw images (coregistration, normalization, brain shift correction, PaCER electrode detection, VTA simulation) and compare with the authors' derivatives.

## What's in here

- `scripts/`: the pipeline, step by step (`01_` to `09b_`), the QC plotting scripts, and the `wp2_*` scripts for the Lead-DBS part.
- `qc/`: the QC figures I looked at before moving on to each next step.
- `wp2_leaddbs/compare/`: contact distances and the rigid transform between my native space and the authors'.

No data is included (it's big, get it from ScienceDB). Paths in the scripts are hardcoded to my machine (a Mac with Docker), so expect to edit them.

## Where it stands

- Tractography runs and looks plausible at the large-tract level.
- My electrode contacts land within about 0.3 mm of the authors', and the STN overlap is high (Dice 0.90-0.96). Both come from PaCER, and the authors also corrected theirs by hand, so this is agreement, not proof of accuracy.
- The first VTA came out about twice too big. The cause was a flipped electrode trajectory in my reconstruction file. With it fixed (in a test copy only) the Dice with the authors' VTA is 0.87 on the right and 0.80 on the left. Re-running their own inputs only gives about 0.9, so that's the ceiling.
