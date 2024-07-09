import argparse
import logging
from datetime import datetime
from pathlib import Path
from smr_mcs.distributions import Uniform

from smr_mcs.config import ScalingOption, SimulationConfig
from smr_mcs.project import load_simulation_projects_from_yaml
from smr_mcs.simulation_runner import run_simulation, run_simulation_concurrent, store_results

parser = argparse.ArgumentParser(
    prog="SMR Monte Carlo Simulator", description="Perform Monte Carlo simulation for SMR costs."
)

parser.add_argument("-p", "--parallel", action="store_true", help="Perform multiprocessing")
parser.add_argument(
    "-s", "--scaling", choices=["manufacturer", "rothwell", "roulstone"], help="SMR Cost scaling method"
)
parser.add_argument("-c", "--config", help="path to yaml-file with the config.", default="config/reference.yaml")
parser.add_argument("-d", "--dataset", help="path to yaml-file with the dataset.", default="data/reference.yaml")
parser.add_argument("-u", "--unit-doubling", help="How many doublings of each unit production.", default=1)

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
    if args.scaling == "manufacturer":
        opt_scaling = ScalingOption.MANUFACTURER
    elif args.scaling == "rothwell":
        opt_scaling = ScalingOption.ROTHWELL
    elif args.scaling == "roulstone":
        opt_scaling = ScalingOption.ROULSTONE

    logger.info("Scaling type: %s", opt_scaling.value)

    start_time = datetime.now()

    def check_and_get_path(path: str):
        dataset_file = Path(path)
        if not dataset_file.exists():
            dataset_file = Path.cwd() / path
            if not dataset_file.exists():
                raise ValueError(f"dataset {path} does not exist")
        return dataset_file

    dataset_file = check_and_get_path(args.dataset)
    config_file = check_and_get_path(args.config)

    logger.info("Reading dataset from %s", dataset_file)
    simulation_projects = load_simulation_projects_from_yaml(file_path=dataset_file)

    logger.info("Reading config from %s", config_file)
    config = SimulationConfig.from_yaml(yaml_file=config_file)
    config.opt_scaling = opt_scaling
    config.unit_doubling = int(args.unit_doubling)

    # Execute the simulation
    logger.info("Running simulation")
    if args.parallel:
        num_processes = 2  # Memory restrictive
        logger.info("Concurrent simulation with %d processes", num_processes)
        npv_results, lcoe_results, inv_results = run_simulation_concurrent(simulation_projects, config, num_processes)
    else:
        logger.info("Sequential simulation")
        npv_results, lcoe_results, inv_results = run_simulation(simulation_projects, config)

    print(lcoe_results.mean())
    # logger.info("LCOE mean: ", lcoe_results.mean() )
    # logger.info("LCOE std: ", lcoe_results.std() )

    logger.info("Storing results")
    store_results(npv_results, lcoe_results, inv_results, config, output_path, simulation_projects)
    logger.info(f"Finished! Took {datetime.now()-start_time}")
