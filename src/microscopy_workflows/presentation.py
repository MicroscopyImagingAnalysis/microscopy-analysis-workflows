"""Small helpers shared by the walkthrough notebooks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from IPython.display import Image, SVG, display


def project_root(start: str | Path | None = None) -> Path:
    """Find the repository root from a notebook or source directory."""
    current = Path(start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / "pyproject.toml").exists() and (candidate / "notebooks").is_dir():
            return candidate
    raise FileNotFoundError("Could not locate the microscopy workflow repository root")


def load_config(name: str, *, root: str | Path | None = None) -> dict:
    """Load a named JSON configuration from the repository."""
    path = project_root(root) / "configs" / name
    return json.loads(path.read_text(encoding="utf-8"))


def show_result(name: str, *, root: str | Path | None = None):
    """Display a generated result, falling back to its reference rendering."""
    repository = project_root(root)
    generated = repository / "figures" / "generated" / name
    reference = repository / "assets" / "results" / name
    path = generated if generated.exists() else reference
    if not path.exists():
        raise FileNotFoundError(f"No generated or reference result named {name!r}")
    rendered = SVG(filename=str(path)) if path.suffix.lower() == ".svg" else Image(filename=str(path))
    display(rendered)
    return path


def describe_paths(paths: Iterable[str | Path]) -> list[dict[str, object]]:
    """Summarize a collection of microscopy input paths before loading images."""
    rows = []
    for value in paths:
        path = Path(value)
        rows.append(
            {
                "name": path.name,
                "suffix": path.suffix.lower(),
                "exists": path.exists(),
                "size_bytes": path.stat().st_size if path.exists() else None,
            }
        )
    return rows
