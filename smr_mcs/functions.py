import numpy as np

from smr_mcs.config import ScalingOption, SimulationConfig
from smr_mcs.project import SimulationProject


def get_rand_investment(pj: SimulationProject, config: SimulationConfig):
    if config.opt_scaling == ScalingOption.MANUFACTURER:
        rand_investment = (
            pj.investment.draw(config.n)
            * pj.plant_capacity.draw(config.n)
            * np.ones(config.n)
            * (1 - pj.learning_factor.draw(config.n))
        )
    elif config.opt_scaling == ScalingOption.ROULSTONE or config.opt_scaling == ScalingOption.UNIFORM:
        rand_investment = (
            pj.reference_pj.investment.draw(config.n)
            * pj.reference_pj.capacity.draw(config.n)
            * (1 - pj.learning_factor.draw(config.n))
            * (pj.plant_capacity.draw(config.n) / pj.reference_pj.capacity.draw(config.n)) ** config.scaling.draw(config.n)
        )
    elif config.opt_scaling == ScalingOption.ROTHWELL:
        rand_investment = (
            pj.reference_pj.investment.draw(config.n)
            * pj.reference_pj.capacity.draw(config.n)
            * (1 - pj.learning_factor.draw(config.n))
            * (pj.plant_capacity.draw(config.n) / pj.reference_pj.capacity.draw(config.n)) ** (1 + np.log2(config.scaling.draw(config.n)))
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
    loadfactor_mask = np.arange(max_operational_time) < operating_time[:, None]
    loadfactor[~loadfactor_mask] = 0.0 
    
    investment = get_rand_investment(pj, config=config)

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
    electricity[operation_mask] = (plant_capacity[:,np.newaxis] * loadfactor * 8760).flatten()
    cash_in[operation_mask] = electricity_price.flatten()*electricity[operation_mask]
    cash_out[operation_mask] = operating_cost_fix.repeat(operating_time) + operating_cost_variable.repeat(operating_time) * electricity[operation_mask]
    
    discount = 1/((1+wacc[:, np.newaxis])**(np.arange(max_time)))
    disc_electricity = electricity*discount
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
        "lcoe": np.sum(disc_cash_out, axis=1) / np.sum(disc_electricity, axis=1)
    }


if __name__ == "__main__":
    # %%
    from pathlib import Path

    import pandas as pd
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

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
    )
    
    for pj in simulation_projects:
        res = mc_run(config=config, pj=pj)

        df_npv[pj.name] = res["npv"] / pj.plant_capacity.draw(1)
        df_lcoe[pj.name] = res["lcoe"]

    
    df_npv.describe()
    df_lcoe.describe()

    # %%
    
    res = npv_lcoe(disc_res)


    def plot_rand_vars(rand_vars):
        # Determine the number of subplots based on the number of keys in rand_vars
        num_vars = len(rand_vars)
        rows = int(num_vars**0.5)  # Arrange plots in a roughly square layout
        cols = -(-num_vars // rows)  # Ceiling division to determine the number of columns

        # Create a subplot figure
        fig = make_subplots(rows=rows, cols=cols, subplot_titles=[f"{key}" for key in rand_vars])

        # Add a histogram to each subplot
        for i, key in enumerate(rand_vars, start=1):
            trace = go.Histogram(x=rand_vars[key].flatten(), nbinsx=100)
            fig.add_trace(trace, row=(i - 1) // cols + 1, col=(i - 1) % cols + 1)

        # Update layout if necessary (e.g., to adjust spacing or add a common title)
        fig.update_layout(title_text=f"Histograms for {pj.name}", showlegend=False)
        fig.show()