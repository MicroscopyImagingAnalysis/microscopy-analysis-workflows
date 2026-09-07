#!/usr/bin/env python3
"""Convert one ordered nuclear crop record into graph and tracking tables."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from nuclear_imaging_core.graph import (
    DenseRegionConfig,
    TrackingConfig,
    build_graph_bundles_for_triplet,
    segment_dense_regions_triplet,
    track_triplet,
)
from nuclear_imaging_core.io import discover_triplet_records, load_frame_crop


def run(
    crop_root: Path,
    record_index: int,
    frame_order: tuple[str, str, str],
    output_dir: Path,
) -> None:
    """Detect dense regions, construct graphs and track nodes for one crop."""
    records = discover_triplet_records(crop_root)
    if records.empty:
        raise ValueError(f"No crop records found below {crop_root}")
    if not 0 <= record_index < len(records):
        raise IndexError(f"record-index {record_index} outside 0..{len(records) - 1}")

    record = records.iloc[record_index]
    frames = load_frame_crop(record["crop_path"], frame_order=frame_order)
    dense_config = DenseRegionConfig(
        threshold_mode="quantile",
        threshold_quantile=80,
        gaussian_sigma_px=1,
        min_region_size_px=20,
        with_boundary_nodes=True,
        boundary_num_points=64,
    )
    frame_results = segment_dense_regions_triplet(
        frames,
        dense_config,
        frame_order=frame_order,
    )
    bundles = build_graph_bundles_for_triplet(frame_results, frame_order=frame_order)
    tracking = track_triplet(
        {name: result.node_table for name, result in frame_results.items()},
        TrackingConfig(w_position=1, w_size=1, candidate_radius_px=20),
        frame_order=frame_order,
        frame_masks={
            name: result.nucleus_mask for name, result in frame_results.items()
        },
    )

    identity_columns = (
        "experiment_id",
        "cell",
        "condition",
        "batch",
        "nd2_prefix",
        "crop_id",
        "crop_path",
    )
    identity = {column: record[column] for column in identity_columns}

    def attach_identity(table: pd.DataFrame) -> pd.DataFrame:
        result = table.copy()
        for column, value in reversed(tuple(identity.items())):
            result.insert(0, column, value)
        return result

    node_tables = [result.node_table for result in frame_results.values()]
    edge_tables = []
    graph_rows = []
    for frame_name, bundle in bundles.items():
        edges = bundle.edge_table.copy()
        edges.insert(0, "frame", frame_name)
        edge_tables.append(edges)
        graph_rows.append({**identity, "frame": frame_name, **bundle.graph_attrs})

    tables = {
        "nodes": attach_identity(pd.concat(node_tables, ignore_index=True)),
        "edges": attach_identity(pd.concat(edge_tables, ignore_index=True)),
        "graph_features": pd.DataFrame(graph_rows),
        "matches_ref_dec": attach_identity(tracking["matches_ref_dec"]),
        "matches_dec_fin": attach_identity(tracking["matches_dec_fin"]),
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    for table_name, table in tables.items():
        table.to_csv(output_dir / f"{table_name}.csv", index=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("crop_root", type=Path)
    parser.add_argument("--record-index", type=int, default=0)
    parser.add_argument(
        "--frame-order",
        nargs=3,
        default=("ref", "dec", "fin"),
        metavar=("FIRST", "SECOND", "THIRD"),
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    run(
        arguments.crop_root,
        arguments.record_index,
        tuple(arguments.frame_order),
        arguments.output_dir,
    )
