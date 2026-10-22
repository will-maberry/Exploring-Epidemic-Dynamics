# Exploring Outbreak Dynamics

This repository documents my exploration of how infectious diseases spread through populations. Throughout the project, I'll use compartmental models, geographic data, and hypothetical public health interventions to investigate outbreak dynamics.

The project follows a hypothetical outbreak of **Slurry-Throat Congestion (STC)**, an entirely fictional disease characterized by the sensation of a thick, sticky, oatmeal-like substance coating the throat.

## Overview

This project is an ongoing exploration of infectious disease modeling, beginning with the classical susceptible–infectious–removed (SIR) model and progressively introducing more complex assumptions about disease transmission and population structure.

Throughout the project, I hope to develop a deeper understanding of the mathematical and computational principles underlying epidemic models, while investigating how different assumptions influence simulated outbreak dynamics.

Areas I plan to explore include:

- **Classical epidemic dynamics:** Transmission and removal rates, reproduction numbers, epidemic thresholds, peak prevalence, and final outbreak size.
- **Population structure and heterogeneity:** Homogeneous versus structured populations, differences in population size, and the effects of initial infection locations.
- **Geographic transmission:** County-level spatial models, neighboring-county transmission, hypothetical long-distance connections, and animated geographic spread.
- **Public health interventions:** Isolation, quarantine, physical distancing, vaccination, and the timing and duration of interventions.
- **Alternative compartmental models:** Extensions of the classical SIR framework, including SEIR models, waning immunity, and additional disease states.
- **Stochastic epidemic modeling:** Random transmission events, outbreak variability, and comparisons between deterministic and stochastic simulations.
- **Sensitivity and uncertainty analysis:** The effects of parameter choices, initial conditions, and model assumptions on simulated outcomes.
- **Model evaluation and limitations:** Numerical behavior, geographic aggregation, and the limitations of interpreting hypothetical simulations.

Not all of these components have been implemented. My goal is to build on each experiment as I become more familiar with the underlying mathematics, modeling approaches, and their limitations.

## Data Sources

The simulations use publicly available geographic and demographic data from the U.S. Census Bureau:

- [2025 Vintage County Population Estimates](https://www.census.gov/data/tables/time-series/demo/popest/2020s-counties-total.html)
- [2025 TIGER/Line Shapefiles](https://www.census.gov/geographies/mapping-files/2025/geo/tiger-line-file.html)

The processed datasets combine county population estimates, geographic identifiers, county boundaries, and shared-border adjacency relationships.

The geographic scope is limited to the **contiguous 48 U.S. states**, excluding Alaska, Hawaii, and Washington, D.C.

Although the simulations use real population and geographic data, transmission parameters, contact patterns, and intervention effects are hypothetical and are not calibrated to observed epidemiological data.

The `Data_Processed` directory contains all of the processed datasets required to run the notebook, while the `dataset_builder.py` documents how these datasets were constructed from the original Census and TIGER/Line files.

## Project Structure

- `SIR_Simulation.ipynb`: Primary notebook containing the models, experiments, visualizations, and explanations.
- `notebook_helpers.py`: Reusable helper functions for the notebook. Placing functions here allows the notebook to focus on the modeling itself.
- `Data_Processed/`: Processed population and geographic datasets used by the notebook.
- `dataset_builder.py`: Preprocessing script used to construct the geographic and population datasets from the original sources.