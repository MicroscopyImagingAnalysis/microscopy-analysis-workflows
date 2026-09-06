# Notebook guide

These notebooks form one production-style methodological walkthrough. Run them
in numeric order when applying the workflow to a new experiment.

- `00` defines the data flow and the boundary between reusable methods and
  experiment-specific choices.
- `01` examines image dimensions and intensity before selecting segmentation.
- `02` builds interpretable object and radial features.
- `03` represents spatial organization as graphs.
- `04` learns complementary VAE/CVAE image representations.
- `05` joins, filters and visualizes the resulting feature tables.

Each computational section is followed by a representative result, so the
relationship between code, intermediate state and interpretation stays visible.
Exploratory parameter trials belong in separate working notebooks; stable
methods and final analysis order belong here.
