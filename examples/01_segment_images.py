#!/usr/bin/env python3
"""Segment one microscopy image and hand its labelled objects to measurement."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from tifffile import imread

from microscopy_workflows import describe_paths, load_config
from nuclear_imaging_core.measurements import describe_image, region_feature_table
from nuclear_imaging_core.segmentation import SegmentationConfig, segment_frame


def run(image_path: Path, config_name: str, output_dir: Path) -> None:
    """Run image inspection, configured segmentation and object measurement."""
    path_record = describe_paths([image_path])[0]
    if not path_record["exists"]:
        raise FileNotFoundError(image_path)

    image = np.asarray(imread(image_path))
    image_record = describe_image(image)
    config = SegmentationConfig(
        **load_config(config_name, root=Path(__file__).resolve())
    )
    labels, foreground = segment_frame(image, config)

    objects = region_feature_table(image, labels)
    objects.insert(
        0,
        "object_id",
        objects["label"].map(lambda label: f"{image_path.stem}-nucleus-{label}"),
    )
    objects.insert(1, "source_image", image_path.name)

    output_dir.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        output_dir / f"{image_path.stem}_segmentation.npz",
        image=image,
        labels=labels,
        foreground=foreground,
    )
    objects.to_csv(output_dir / f"{image_path.stem}_objects.csv", index=False)
    print({"path": path_record, "image": image_record, "objects": len(objects)})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path, help="Input TIFF image or stack")
    parser.add_argument(
        "--config",
        default="segmentation_2d.json",
        choices=("segmentation_2d.json", "segmentation_3d.json"),
        help="Pixel-based segmentation configuration",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    run(arguments.image, arguments.config, arguments.output_dir)
