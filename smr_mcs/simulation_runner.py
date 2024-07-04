import hashlib
import json
import multiprocessing as mp
from logging import getLogger
from pathlib import Path

import pandas as pd

from smr_mcs.config import SimulationConfig
from smr_mcs.functions import mc_run
from smr_mcs.project import SimulationProject

logger = getLogger(__name__)


def simulate_project(pj, config):
    logger.info(f"Running simulation for project: {pj.name}")
    results = mc_run(config=config, pj=pj)
    logger.info(f"Done with simulation for project: {pj.name}")
    return pj.name, results["npv"], results["lcoe"]


def run_simulation_concurrent(
    pjs: list[SimulationProject], config: SimulationConfig, num_processes: int
) -> tuple[pd.DataFrame, pd.DataFrame]:
    logger.info(f"Running {num_processes} processes.")

    with mp.Pool(processes=num_processes) as pool:
        results = pool.starmap(simulate_project, [(pj, config) for pj in pjs])

    npv_results = pd.DataFrame()
    lcoe_results = pd.DataFrame()

    for result in results:
        pj_name, npv, lcoe = result
        npv_results[pj_name] = npv
        lcoe_results[pj_name] = lcoe

    return npv_results, lcoe_results


def run_simulation(pjs: list[SimulationProject], config: SimulationConfig) -> tuple[pd.DataFrame, pd.DataFrame]:
    npv_results = pd.DataFrame()
    lcoe_results = pd.DataFrame()

    for i, pj in enumerate(pjs):
        logger.info(f"Running simulation for project {i}: {pj.name}")

        results = mc_run(config=config, pj=pj)

        npv_results[pj.name] = results["npv"]
        lcoe_results[pj.name] = results["lcoe"]

    return npv_results, lcoe_results


def stable_hash(s: str) -> str:
    """Generate a stable hash for a given string using SHA-256."""
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def store_results(
    npv_results, lcoe_results, config: SimulationConfig, output_path: Path, simulation_projects: list[SimulationProject]
):
    # Summary statistics
    npv_summary = npv_results.describe()
    lcoe_summary = lcoe_results.describe()

    dataset_str = "\n".join(map(str, simulation_projects))
    config_str = str(config.to_dict())

    dataset_path = output_path / stable_hash(dataset_str)
    config_path = dataset_path / config.opt_scaling.value / stable_hash(config_str)

    dataset_path.mkdir(exist_ok=True, parents=True)
    config_path.mkdir(exist_ok=True, parents=True)

    with open(dataset_path / "dataset.txt", "w") as file:
        file.write(dataset_str)

    with open(config_path / "config.json", "w") as file:
        json.dump(config.to_dict(), file, indent=4)

    npv_results.to_csv(config_path / "npv_results.csv", index=False)
    npv_summary.to_csv(config_path / "npv_summary.csv", index=True)
    lcoe_results.to_csv(config_path / "lcoe_results.csv", index=False)
    lcoe_summary.to_csv(config_path / "lcoe_summary.csv", index=True)
