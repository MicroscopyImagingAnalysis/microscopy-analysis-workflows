#!/usr/bin/env python3
"""Fit a VAE from an existing manifest and export reconstructions and features."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from tifffile import imread
from torch.utils.data import DataLoader, Dataset

from nuclear_vae_embeddings import fit_vae, latent_feature_table, reconstruct_images
from nuclear_vae_embeddings.models import VAE


class ManifestCropDataset(Dataset):
    """Read 64 × 64 crops while preserving caller-supplied row identity."""

    def __init__(
        self,
        rows: pd.DataFrame,
        manifest_directory: Path,
        path_column: str,
        id_column: str,
        metadata_columns: tuple[str, ...],
    ) -> None:
        self.rows = rows.reset_index(drop=True).copy()
        self.manifest_directory = manifest_directory
        self.path_column = path_column
        self.id_column = id_column
        self.metadata_columns = metadata_columns

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int) -> dict[str, object]:
        row = self.rows.iloc[index]
        crop_path = Path(str(row[self.path_column]))
        if not crop_path.is_absolute():
            crop_path = self.manifest_directory / crop_path
        image = np.asarray(imread(crop_path), dtype=np.float32)
        if image.shape != (64, 64):
            raise ValueError(f"Expected a 64 × 64 crop, got {image.shape}: {crop_path}")
        maximum = float(np.max(image))
        if maximum > 0:
            image = image / maximum

        sample: dict[str, object] = {
            "image": torch.from_numpy(image).reshape(1, 64, 64),
            self.id_column: str(row[self.id_column]),
        }
        for column in self.metadata_columns:
            sample[column] = "" if pd.isna(row[column]) else str(row[column])
        return sample


def run(arguments: argparse.Namespace) -> None:
    """Consume existing split labels; do not create or modify a train/test split."""
    torch.manual_seed(arguments.seed)
    manifest = pd.read_csv(arguments.manifest)
    required = {arguments.path_column, arguments.id_column, arguments.split_column}
    missing = sorted(required - set(manifest.columns))
    if missing:
        raise KeyError(f"Manifest is missing required columns: {missing}")

    metadata_columns = tuple(
        column for column in ("condition", "batch") if column in manifest.columns
    )
    dataset_args = (
        arguments.manifest.parent,
        arguments.path_column,
        arguments.id_column,
        metadata_columns,
    )
    split_values = manifest[arguments.split_column].astype(str)
    train_rows = manifest.loc[split_values == arguments.train_label]
    validation_rows = manifest.loc[split_values == arguments.validation_label]
    if train_rows.empty or validation_rows.empty:
        raise ValueError("The requested train and validation split labels must both exist")

    train_dataset = ManifestCropDataset(train_rows, *dataset_args)
    validation_dataset = ManifestCropDataset(validation_rows, *dataset_args)
    feature_dataset = ManifestCropDataset(manifest, *dataset_args)
    train_loader = DataLoader(
        train_dataset,
        batch_size=arguments.batch_size,
        shuffle=True,
    )
    validation_loader = DataLoader(
        validation_dataset,
        batch_size=arguments.batch_size,
        shuffle=False,
    )
    feature_loader = DataLoader(
        feature_dataset,
        batch_size=arguments.batch_size,
        shuffle=False,
    )

    model = VAE(
        nc=1,
        ngf=arguments.base_channels,
        ndf=arguments.base_channels,
        latent_variable_size=arguments.latent_dimensions,
        imsize=64,
        lamb=arguments.kl_weight,
        batchnorm=False,
    )
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=arguments.learning_rate,
        weight_decay=arguments.weight_decay,
    )
    history = fit_vae(
        model,
        train_loader,
        optimizer,
        epochs=arguments.epochs,
    )

    validation_batch = next(iter(validation_loader))
    reconstructions = reconstruct_images(
        model,
        validation_batch["image"],
        use_mean=True,
    )
    latent_table = latent_feature_table(
        model,
        feature_loader,
        id_key=arguments.id_column,
        metadata_keys=metadata_columns,
        feature_prefix="latent_",
    )

    arguments.output_dir.mkdir(parents=True, exist_ok=True)
    history.to_csv(arguments.output_dir / "training_history.csv", index=False)
    latent_table.to_csv(arguments.output_dir / "latent_features.csv", index=False)
    np.savez_compressed(
        arguments.output_dir / "validation_reconstructions.npz",
        inputs=validation_batch["image"].numpy(),
        reconstructions=reconstructions.numpy(),
        object_ids=np.asarray(validation_batch[arguments.id_column]),
    )
    torch.save(
        {"state_dict": model.state_dict()},
        arguments.output_dir / "vae_model.pt",
    )

    if arguments.features_table is not None:
        measured = pd.read_csv(arguments.features_table)
        combined = measured.merge(
            latent_table,
            on=arguments.id_column,
            validate="one_to_one",
        )
        combined.to_csv(arguments.output_dir / "representations.csv", index=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--features-table", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--path-column", default="crop_path")
    parser.add_argument("--id-column", default="object_id")
    parser.add_argument("--split-column", default="split")
    parser.add_argument("--train-label", default="train")
    parser.add_argument("--validation-label", default="validation")
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--base-channels", type=int, default=128)
    parser.add_argument("--latent-dimensions", type=int, default=128)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--weight-decay", type=float, default=1e-5)
    parser.add_argument("--kl-weight", type=float, default=1e-5)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
