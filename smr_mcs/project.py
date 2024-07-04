from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import yaml

from smr_mcs.distributions import Degenerate, Distribution, Gaussian, Triangular, Uniform


@dataclass(frozen=True)
class ProjectTime:
    construction: float
    operating: float


@dataclass(frozen=True)
class LoadFactor:
    lower: float
    upper: float


@dataclass(frozen=True)
class OperatingCost:
    fixed: float
    variable: float
    fuel: float


@dataclass(frozen=True)
class ReferenceReactor:
    investment: float
    capacity: float


@dataclass(frozen=True)
class Project:
    """
    Represents an investment project.

    :param name: Investment concept.
    :param reactor_type: Investment type.
    :param investment: Investment estimate by manufacturer [USD/MW].
    :param plant_capacity: Plant capacity [MW].
    :param learning_factor: Learning factor.
    :param time: Project time [years] (construction time, plant lifetime).
    :param loadfactor: Load factor, lower, and upper bound of rand variable.
    :param operating_cost: O&M cost (O&M fix cost [USD/MW], O&M variable cost [USD/MWh], fuel cost [USD/MWh]).
    :param reference_pj: Reference reactor (investment costs [USD/MW], plant capacity [MW]).
    """

    name: str
    reactor_type: str
    investment: float
    plant_capacity: float
    learning_factor: float
    time: ProjectTime
    loadfactor: LoadFactor
    operating_cost: OperatingCost
    reference_pj: ReferenceReactor


@dataclass(frozen=True)
class SimulationProjectTime:
    construction: Distribution
    operating: Distribution


@dataclass(frozen=True)
class SimulationOperatingCost:
    fixed: Distribution
    variable: Distribution
    fuel: Distribution


@dataclass(frozen=True)
class SimulationReferenceReactor:
    investment: Distribution
    capacity: Distribution


@dataclass(frozen=True)
class SimulationProject:
    """
    Class used during simulation of a project.

    :param name: Investment concept.
    :param reactor_type: Investment type.
    :param investment: Investment estimate by manufacturer [USD/MW].
    :param plant_capacity: Plant capacity [MW].
    :param learning_factor: Learning factor.
    :param time: Project time [years] (construction time, plant lifetime).
    :param loadfactor: Load factor, lower, and upper bound of rand variable.
    :param operating_cost: O&M cost (O&M fix cost [USD/MW], O&M variable cost [USD/MWh], fuel cost [USD/MWh]).
    :param reference_pj: Reference reactor (investment costs [USD/MW], plant capacity [MW]).
    """

    name: str
    reactor_type: str
    investment: Distribution
    plant_capacity: Distribution
    learning_factor: Distribution
    time: SimulationProjectTime
    loadfactor: Distribution
    operating_cost: SimulationOperatingCost
    reference_pj: SimulationReferenceReactor


def get_projects(df_projects: pd.DataFrame) -> list[Project]:
    pjs = []
    for _, row in df_projects.iterrows():
        pjs.append(
            Project(
                name=row["name"],
                reactor_type=row["type"],
                investment=row["investment"],
                plant_capacity=row["plant_capacity"],
                learning_factor=row["learning_factor"],
                time=ProjectTime(row["construction_time"], row["operating_time"]),
                loadfactor=LoadFactor(row["loadfactor_lower"], row["loadfactor_upper"]),
                operating_cost=OperatingCost(
                    row["operating_cost_fix"], row["operating_cost_variable"], row["operating_cost_fuel"]
                ),
                reference_pj=ReferenceReactor(row["reference_pj_investment"], row["reference_pj_capacity"]),
            )
        )
    return pjs


def create_distribution(data):
    """
    Create a Distribution object based on data.
    """
    distribution_type = data["type"]
    if distribution_type == "Degenerate":
        value = data["value"]
        return Degenerate(value)
    elif distribution_type == "Uniform":
        lower = data["lower"]
        upper = data["upper"]
        seed = data.get("seed", 1)  # Default seed
        return Uniform(lower=lower, upper=upper, seed=seed)
    elif distribution_type == "Gaussian":
        mean = data["mean"]
        std = data["std"]
        seed = data.get("seed", None)  # Default seed None for Gaussian
        return Gaussian(mean=mean, std=std, seed=seed)
    elif distribution_type == "Triangular":
        left = data["left"]
        mode = data["mode"]
        right = data["right"]
        seed = data.get("seed", 1)  # Default seed
        return Triangular(left=left, mode=mode, right=right, seed=seed)
    else:
        raise ValueError(f"Unknown distribution type: {distribution_type}")


def load_simulation_projects_from_yaml(file_path: Path):
    with open(file_path, "r") as yaml_file:
        data = yaml.safe_load(yaml_file)

    simulation_projects = []
    for project_data in data:
        # Create SimulationProject instance
        simulation_project = SimulationProject(
            name=project_data["name"],
            reactor_type=project_data["reactor_type"],
            investment=create_distribution(project_data["investment"]),
            plant_capacity=create_distribution(project_data["plant_capacity"]),
            learning_factor=create_distribution(project_data["learning_factor"]),
            time=SimulationProjectTime(
                construction=create_distribution(project_data["time"]["construction"]),
                operating=create_distribution(project_data["time"]["operating"]),
            ),
            loadfactor=create_distribution(project_data["loadfactor"]),
            operating_cost=SimulationOperatingCost(
                fixed=create_distribution(project_data["operating_cost"]["fixed"]),
                variable=create_distribution(project_data["operating_cost"]["variable"]),
                fuel=create_distribution(project_data["operating_cost"]["fuel"]),
            ),
            reference_pj=SimulationReferenceReactor(
                investment=create_distribution(project_data["reference_pj"]["investment"]),
                capacity=create_distribution(project_data["reference_pj"]["capacity"]),
            ),
        )
        simulation_projects.append(simulation_project)

    return simulation_projects
