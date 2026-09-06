import ast
from collections import Counter
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_walkthrough_notebooks_have_clear_progression_and_valid_code():
    notebooks = sorted((ROOT / "notebooks").glob("[0-9][0-9]_*.ipynb"))
    assert [path.name[:2] for path in notebooks] == ["00", "01", "02", "03", "04", "05"]
    for path in notebooks:
        notebook = json.loads(path.read_text(encoding="utf-8"))
        cells = notebook["cells"]
        assert cells[0]["cell_type"] == "markdown"
        assert "Notebook role:" in "".join(cells[0]["source"])
        assert sum(cell["cell_type"] == "code" for cell in cells) >= 2
        assert any("Representative result" in "".join(cell.get("source", [])) for cell in cells)
        for cell in cells:
            if cell["cell_type"] == "code":
                ast.parse("".join(cell.get("source", [])), filename=str(path))
                assert cell.get("outputs", []) == []
                assert cell.get("execution_count") is None


def test_all_markdown_result_assets_exist():
    for path in (ROOT / "notebooks").glob("*.ipynb"):
        notebook = json.loads(path.read_text(encoding="utf-8"))
        source = "\n".join("".join(cell.get("source", [])) for cell in notebook["cells"])
        links = re.findall(r"!\[[^]]*\]\(([^)]+)\)", source)
        assert links
        for relative in links:
            asset = (path.parent / relative).resolve()
            assert asset.is_file() and asset.stat().st_size > 0


def test_reference_results_are_not_reused_between_notebooks():
    references = []
    for path in (ROOT / "notebooks").glob("[0-9][0-9]_*.ipynb"):
        notebook = json.loads(path.read_text(encoding="utf-8"))
        source = "\n".join("".join(cell.get("source", [])) for cell in notebook["cells"])
        references.extend(
            relative
            for relative in re.findall(r"!\[[^]]*\]\(([^)]+)\)", source)
            if "/assets/results/" in relative
        )
    duplicates = [reference for reference, count in Counter(references).items() if count > 1]
    assert duplicates == []
