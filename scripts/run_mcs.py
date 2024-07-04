import argparse
import logging
from datetime import datetime
from pathlib import Path

from smr_mcs.config import ScalingOption, SimulationConfig
from smr_mcs.distributions import Gaussian, Triangular, Uniform
from smr_mcs.project import load_simulation_projects_from_yaml
from smr_mcs.simulation_runner import run_simulation, run_simulation_concurrent, store_results

parser = argparse.ArgumentParser(
    prog="SMR Monte Carlo Simulator", description="Perform Monte Carlo simulation for SMR costs."
)

parser.add_argument("-c", "--concurrent", action="store_true", help="Perform multiprocessing")

args = parser.parse_args()

# Set output paths
output_path = Path.cwd() / "results"

# Configure logging
logger = logging.getLogger("smr_mcs")

logger.setLevel(logging.INFO)  # Set the logger's level

# Create a file handler for writing logs to a file
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

file_handler = logging.FileHandler(output_path / "monte_carlo_simulation.log", mode="a")
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)


if __name__ == "__main__":
    start_time = datetime.now()
    config = SimulationConfig(
        n=1000000,
        electricity_price=Uniform(lower=52.2, upper=95.8),
        wacc=Uniform(lower=0.04,upper=0.10),
        scaling=Uniform(lower=0.20, upper=0.75),
        opt_scaling=ScalingOption.ROTHWELL,
    )

    yaml_file = Path.cwd() / "data/reference.yaml"
    simulation_projects = load_simulation_projects_from_yaml(file_path=yaml_file)

    # Execute the simulation
    logger.info("Running simulation")
    if args.concurrent:
        num_processes = 3  # Memory restrictive
        npv_results, lcoe_results = run_simulation_concurrent(simulation_projects, config, num_processes)
    else:
        npv_results, lcoe_results = run_simulation(simulation_projects, config)

    logger.info("Storing results")
    store_results(npv_results, lcoe_results, config, output_path, simulation_projects)
    logger.info(f"Finished! Took {datetime.now()-start_time}")
