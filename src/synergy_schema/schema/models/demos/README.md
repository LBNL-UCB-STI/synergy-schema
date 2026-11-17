# DEMOS model schemas

This directory contains two distinct DEMOS schema slices:

- `demos_core.yaml`: Authoritative core DEMOS native HDF5 (`persons`, `households`)
  and CSV calibration/control (`income_rates`, `hsize_ct`,
  `observed_marrital_data`, `observed_calibration_counts`) I/O contracts,
  derived from `NatLabRockies/DEMOS` (`demos/config.py`, `demos/datasources.py`,
  `demos/models/`, and `data/small_example/small_example_tables.h5`).
- `demos_polaris_mapped_examples.yaml`: Provisional LinkML slice for observed
  `POLARIS_mapped` CSV exports (`Household2018_POLARIS_mapped.csv` and
  `Person2018_POLARIS_mapped.csv`). Crosswalks between core DEMOS and
  POLARIS-mapped tables belong in `../../mappings/` once the preprocessing and
  postprocessing translation scripts are finalized.
