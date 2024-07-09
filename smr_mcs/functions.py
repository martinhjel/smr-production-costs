import sys

import numpy as np

from smr_mcs.config import ScalingOption, SimulationConfig
from smr_mcs.distributions import Uniform
from smr_mcs.project import SimulationProject, load_simulation_projects_from_yaml


def get_rand_investment(pj: SimulationProject, config: SimulationConfig, plant_capacity: np.ndarray):
    learning_rate = (1 - pj.learning_factor.draw(config.n)) ** float(config.unit_doubling)
    reference_capacity = pj.reference_pj.capacity.draw(config.n)
    if config.opt_scaling == ScalingOption.MANUFACTURER:
        rand_investment = pj.investment.draw(config.n) * plant_capacity * learning_rate
    elif config.opt_scaling == ScalingOption.ROULSTONE:
        beta = config.scaling.draw(config.n)
        rand_investment = (
            pj.reference_pj.investment.draw(config.n)
            * reference_capacity
            * learning_rate
            * (plant_capacity / reference_capacity) ** beta
        )
    elif config.opt_scaling == ScalingOption.ROTHWELL:
        beta = config.scaling.draw(config.n)
        # gamma = np.power(2, beta - 1) # NB:
        gamma = beta
        rand_investment = (
            pj.reference_pj.investment.draw(config.n)
            * reference_capacity
            * learning_rate
            * (plant_capacity / reference_capacity) ** (1 + np.log2(gamma))
        )
    else:
        raise ValueError("Option for the scaling method is unknown.")
    return rand_investment


def mc_run(config: SimulationConfig, pj: SimulationProject) -> dict:
    """
    Performs a Monte Carlo simulation for an investment project.

    :param config: Simulation config.
    :param pj: Project instance.
    :return: Dictionary of simulation results.
    """
    construction_time = pj.time.construction.draw(config.n).astype(int)
    operating_time = pj.time.operating.draw(config.n).astype(int)
    total_time = construction_time + operating_time
    max_time = int(max(total_time))
    max_operational_time = int(max(operating_time))

    plant_capacity = pj.plant_capacity.draw(config.n)

    wacc = config.wacc.draw(config.n)
    electricity_price = config.electricity_price.draw((config.n, max_operational_time))
    loadfactor = pj.loadfactor.draw((config.n, max_operational_time))

    investment = get_rand_investment(pj, config=config, plant_capacity=plant_capacity)

    operating_cost_fix = plant_capacity * pj.operating_cost.fixed.draw(config.n)
    operating_cost_variable = pj.operating_cost.variable.draw(config.n) + pj.operating_cost.fuel.draw(config.n)

    cash_in = np.zeros((config.n, max_time))
    cash_out = np.zeros((config.n, max_time))
    cash_net = np.zeros((config.n, max_time))
    disc_cash_out = np.zeros((config.n, max_time))
    disc_cash_net = np.zeros((config.n, max_time))
    electricity = np.zeros((config.n, max_time))
    disc_electricity = np.zeros((config.n, max_time))

    time_indices = np.arange(max_time)
    construction_mask = time_indices < construction_time[:, None]
    operation_end_time = construction_time + operating_time
    operation_mask = (time_indices >= construction_time[:, None]) & (time_indices < operation_end_time[:, None])

    # Construction stage
    cash_out[construction_mask] = (investment / construction_time).repeat(construction_time)

    # Operational stage
    electricity[operation_mask] = (plant_capacity[:, np.newaxis] * loadfactor * 8760).flatten()
    cash_in[operation_mask] = electricity_price.flatten() * electricity[operation_mask]
    cash_out[operation_mask] = (
        operating_cost_fix.repeat(operating_time)
        + operating_cost_variable.repeat(operating_time) * electricity[operation_mask]
    )

    discount = 1 / ((1 + wacc[:, np.newaxis]) ** (np.arange(max_time)))
    disc_electricity = electricity * discount
    cash_net = cash_in - cash_out
    disc_cash_out = cash_out * discount
    disc_cash_net = cash_net * discount

    return {
        "disc_cash_out": disc_cash_out,
        "disc_cash_net": disc_cash_net,
        "disc_electricity": disc_electricity,
        "wacc": wacc,
        "electricity_price": electricity_price,
        "loadfactor": loadfactor,
        "investment": investment,
        "npv": np.sum(disc_cash_net, axis=1) / plant_capacity,
        "lcoe": np.sum(disc_cash_out, axis=1) / np.sum(disc_electricity, axis=1),
    }


def get_total_size(obj, seen=None):
    """Recursively find the total memory size of an object."""
    size = sys.getsizeof(obj)
    if seen is None:
        seen = set()
    obj_id = id(obj)
    if obj_id in seen:
        return 0
    seen.add(obj_id)

    if isinstance(obj, dict):
        size += sum(get_total_size(v, seen) for v in obj.values())
        size += sum(get_total_size(k, seen) for k in obj.keys())
    elif hasattr(obj, "__dict__"):
        size += get_total_size(vars(obj), seen)
    elif hasattr(obj, "__iter__") and not isinstance(obj, (str, bytes, bytearray)):
        size += sum(get_total_size(i, seen) for i in obj)

    return size


if __name__ == "__main__":
    # %%
    from pathlib import Path

    import pandas as pd

    from smr_mcs.distributions import Gaussian, Triangular, Uniform
    from smr_mcs.project import load_simulation_projects_from_yaml

    yaml_file = Path.cwd() / "data/reference.yaml"
    simulation_projects = load_simulation_projects_from_yaml(file_path=yaml_file)

    df_npv = pd.DataFrame()
    df_lcoe = pd.DataFrame()

    config = SimulationConfig(
        n=1000000,
        electricity_price=Gaussian(mean=70, std=30),
        wacc=Triangular(left=0.04, mode=0.06, right=0.12),
        scaling=Uniform(lower=0.20, upper=0.75),
        opt_scaling=ScalingOption.ROTHWELL,
        unit_doubling=1,
    )

    for pj in simulation_projects:
        res = mc_run(config=config, pj=pj)

        df_npv[pj.name] = res["npv"] / pj.plant_capacity.draw(1)
        df_lcoe[pj.name] = res["lcoe"]

    df_npv.describe()
    df_lcoe.describe()
