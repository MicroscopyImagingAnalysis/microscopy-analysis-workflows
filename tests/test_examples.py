import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
EXPECTED_SCRIPTS = {
    "01_segment_images.py": ("segment_frame", "region_feature_table"),
    "02_spheroid_radial_analysis.py": ("measure_spheroid_system", "analyze_radial_2d"),
    "03_spatial_graph_analysis.py": ("segment_dense_regions_triplet", "track_triplet"),
    "04_vae_representations.py": ("fit_vae", "latent_feature_table", "reconstruct_images"),
}


def test_run_mode_scripts_are_parseable_and_expose_expected_calls():
    scripts = {path.name for path in EXAMPLES.glob("[0-9][0-9]_*.py")}
    assert scripts == set(EXPECTED_SCRIPTS)
    for name, expected_calls in EXPECTED_SCRIPTS.items():
        source = (EXAMPLES / name).read_text(encoding="utf-8")
        ast.parse(source, filename=name)
        assert 'if __name__ == "__main__":' in source
        for call in expected_calls:
            assert call in source


def test_run_mode_examples_do_not_contain_stored_outputs():
    allowed_suffixes = {".md", ".py"}
    files = [path for path in EXAMPLES.rglob("*") if path.is_file()]
    assert files
    assert all(path.suffix in allowed_suffixes for path in files)


def test_readme_links_each_script_to_its_walkthrough():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for script in EXPECTED_SCRIPTS:
        assert f"examples/{script}" in readme
    for notebook in (
        "01_images_and_segmentation.ipynb",
        "02_object_and_radial_features.ipynb",
        "03_spatial_graphs.ipynb",
        "04_vae_representations.ipynb",
    ):
        assert f"notebooks/{notebook}" in readme
