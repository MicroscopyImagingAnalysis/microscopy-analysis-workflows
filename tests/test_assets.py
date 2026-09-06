from pathlib import Path
import re
from xml.etree import ElementTree

import sys


ROOT = Path(__file__).resolve().parents[1]


def test_result_images_are_valid_png_files():
    images = sorted((ROOT / "assets/results").glob("*.png"))
    assert len(images) >= 5
    for path in images:
        assert path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")


def test_diagrams_are_valid_svg_files():
    diagrams = sorted((ROOT / "assets/diagrams").glob("*.svg"))
    assert len(diagrams) >= 2
    for path in diagrams:
        root = ElementTree.parse(path).getroot()
        assert root.tag.endswith("svg")


def test_result_resolution_prefers_generated_and_falls_back(tmp_path):
    sys.path.insert(0, str(ROOT / "src"))
    from microscopy_workflows.presentation import show_result

    (tmp_path / "notebooks").mkdir()
    (tmp_path / "assets/results").mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text("[project]\nname='test'\n")
    reference = tmp_path / "assets/results/result.png"
    reference.write_bytes(b"\x89PNG\r\n\x1a\n")
    assert show_result("result.png", root=tmp_path) == reference

    generated = tmp_path / "figures/generated/result.png"
    generated.parent.mkdir(parents=True)
    generated.write_bytes(b"\x89PNG\r\n\x1a\n")
    assert show_result("result.png", root=tmp_path) == generated


def test_readme_image_links_are_local_and_resolve():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    links = re.findall(r"!\[[^]]+\]\(([^)]+)\)", readme)
    assert len(links) >= 8
    for relative in links:
        assert not relative.startswith(("http://", "https://", "/"))
        assert (ROOT / relative).is_file()
