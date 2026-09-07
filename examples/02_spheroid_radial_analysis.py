#!/usr/bin/env python3
"""Measure aligned nuclear and spheroid labels and summarize radial structure."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from tifffile import imread

from microscopy_workflows import load_config
from nuclear_spheroid_analysis import (
    analyze_radial_2d,
    analyze_radial_3d,
    measure_spheroid_system,
)


def run(
    nuclear_image_path: Path,
    nuclear_labels_path: Path,
    spheroid_labels_path: Path,
    config_name: str,
    output_dir: Path,
) -> None:
    """Measure a 2D or 3D spheroid system without changing pixel units."""
    nuclear_image = np.asarray(imread(nuclear_image_path))
    nuclear_labels = np.asarray(imread(nuclear_labels_path))
    spheroid_labels = np.asarray(imread(spheroid_labels_path))

    nuclei, spheroids = measure_spheroid_system(
        nuclear_image,
        nuclear_labels,
        spheroid_labels,
    )
    nuclei["DAPI_intensity-mean"] = nuclei["intensity-mean"]

    radial_config = load_config(config_name, root=Path(__file__).resolve())
    radial_function = analyze_radial_2d if nuclear_image.ndim == 2 else analyze_radial_3d
    radial, nuclei, spheroids = radial_function(
        nuclei,
        spheroids,
        nuclear_labels,
        spheroid_labels,
        radial_config,
        {},
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    nuclei.to_csv(output_dir / "nuclei_with_spheroids.csv", index=False)
    spheroids.to_csv(output_dir / "spheroids.csv", index=False)
    radial.to_csv(output_dir / "spheroid_radial_features.csv", index=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nuclear-image", type=Path, required=True)
    parser.add_argument("--nuclear-labels", type=Path, required=True)
    parser.add_argument("--spheroid-labels", type=Path, required=True)
    parser.add_argument("--config", default="spheroid_radial.json")
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    run(
        arguments.nuclear_image,
        arguments.nuclear_labels,
        arguments.spheroid_labels,
        arguments.config,
        arguments.output_dir,
    )
