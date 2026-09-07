# Run-mode examples

These scripts are concise entry points for the four principal analysis routes.
They contain no stored execution state, bundled datasets or committed outputs.
Each script accepts existing inputs and writes only to an explicit
`--output-dir`.

| Script | Required input contract | Runtime products |
| --- | --- | --- |
| `01_segment_images.py` | One 2D image or 3D stack plus a repository JSON segmentation config | Compressed image/label/mask artifact and object table |
| `02_spheroid_radial_analysis.py` | Aligned intensity, nuclear-label and spheroid-label images | Nuclear, spheroid and radial tables |
| `03_spatial_graph_analysis.py` | Crop tree discoverable by `discover_triplet_records()` | Node, edge, graph-summary and temporal-match tables |
| `04_vae_representations.py` | CSV manifest with caller-defined `train` and `validation` rows | Model state, loss history, reconstruction tensors and latent table |

Install the workflow and method packages as described in the repository root,
then inspect a command without processing data:

```bash
python examples/01_segment_images.py --help
python examples/02_spheroid_radial_analysis.py --help
python examples/03_spatial_graph_analysis.py --help
python examples/04_vae_representations.py --help
```

The VAE manifest must contain `crop_path`, `object_id` and `split`. Optional
`condition` and `batch` columns are copied into the latent table. Relative crop
paths are resolved from the manifest directory; the script consumes the split
labels as supplied and does not create a new split.
