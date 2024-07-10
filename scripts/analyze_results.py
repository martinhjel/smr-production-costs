# %%
import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import pyperclip

from scripts.case_studies import get_project_data
from smr_mcs.config import ScalingOption


def get_result_path(dataset: str, scaling_type: ScalingOption, conf_hash: str) -> Path:
    results_path = Path.cwd() / f"results/{dataset}/{scaling_type.value}"
    results = [i for i in results_path.glob("*")]

    for r in results:
        if conf_hash == r.name[: len(conf_hash)]:
            return r


def get_result_paths(dataset: str, scaling_type: ScalingOption) -> list[Path]:
    results_path = Path.cwd() / f"results/{dataset}/{scaling_type.value}"
    return [i for i in results_path.glob("*") if i.is_dir()]


def find_unit_doublings(dataset: str, scaling_type: ScalingOption) -> dict[int, str]:
    """
    Searches through subfolders to find config.json files and extracts
    the value of "unit_doubling".

    :param str: The uid of the dataset.
    :return: A dictionary with unit doubling values as keys and subfolder names as values.
    """
    unit_doublings_dict = {}

    res_paths = get_result_paths(dataset, scaling_type)

    for res in res_paths:
        config_file = res / "config.json"
        if config_file.exists():
            with open(config_file, "r") as file:
                config = json.load(file)
                if "unit_doubling" in config:
                    unit_doublings_value = config["unit_doubling"]
                    unit_doublings_dict[unit_doublings_value] = res.name

    return unit_doublings_dict


#%%

dataset = "c73849526116524e476167d80f974735efba04b6456eadb2fcd85e543d991e51"
scaling_type = ScalingOption.ROTHWELL
conf_hash = "79"


result_path = get_result_path(dataset, scaling_type, conf_hash)
df_projects = get_project_data()

df_lcoe = pd.read_csv(result_path / "lcoe_results.csv")
df_inv = pd.read_csv(result_path / "investment_results.csv")
df_npv = pd.read_csv(result_path / "npv_results.csv")

for col in df_inv.columns:
    ind = df_projects[df_projects["name"] == col].index[0]
    df_inv[col] = df_inv[col] / df_projects.loc[ind, "plant_capacity"]


# %%

def get_norm_investment(dataset, scaling_type, conf_hash):
    result_path = get_result_path(dataset, scaling_type, conf_hash)

    df_inv = pd.read_csv(result_path / "investment_results.csv")

    for col in df_inv.columns:
        ind = df_projects[df_projects["name"] == col].index[0]
        df_inv[col] = df_inv[col] / df_projects.loc[ind, "plant_capacity"]

    return df_inv


df_inv_manuf = get_norm_investment(dataset, ScalingOption.MANUFACTURER, conf_hash)

manufacturer = go.Scatter(
    y=df_inv_manuf.columns,
    x=df_inv_manuf.iloc[0, :],
    mode="markers",
    marker=dict(color="red", size=10),
    name="Manufacturer",
)


df_inv_roth = get_norm_investment(dataset, scaling_type=ScalingOption.ROTHWELL, conf_hash=conf_hash)
df_inv_roul = get_norm_investment(dataset, scaling_type=ScalingOption.ROULSTONE, conf_hash=conf_hash)


def get_bar(df_inv, name="", color="blue"):
    min_values = df_inv.min()
    max_values = df_inv.max()
    heights = [max_val - min_val for min_val, max_val in zip(min_values, max_values)]

    return go.Bar(
        y=df_inv.columns,  # Categories for the x-axis
        x=heights,  # Heights of the bars
        orientation="h",
        base=min_values,
        marker=dict(color=color),
        name=name,
    )


roth = get_bar(df_inv_roth, "Rothwell", color="green")
roul = get_bar(df_inv_roul, "Roulestone", color="blue")

fig = go.Figure(
    data=[manufacturer, roul, roth],
    layout=dict(xaxis=dict(title="USD/MW", type="log")),
)
fig.show()
# %%

scaling_type = ScalingOption.ROULSTONE

result_path = get_result_path(dataset, scaling_type, conf_hash)

df_lcoe = pd.read_csv(result_path / "lcoe_results.csv")
df_lcoe.describe().T


# %%

df_npv = pd.read_csv(result_path / "npv_results.csv")
df_npv.describe().T


# %%

# dataset_adjusted = "4bb862bf0843fd7886dcf4ab37f75f4cf1f679116b75389aa231b42104f54d34" # Gaussian
# dataset_adjusted = "54dfdf28656ad56b513fa810fdda01fbc9fc77cef030bd4f2440b27b194413ee" # Triangular
dataset_adjusted = "01bd434ce47dbaf113ce879b8e3e092b54fbd27b391215a821ed18220f3510cd" # Triangular + OPEX
conf_hash = "9c"
df_inv_roth = get_norm_investment(dataset_adjusted, scaling_type=ScalingOption.ROTHWELL, conf_hash=conf_hash)
roth_imp = get_bar(df_inv_roth, "Rothwell_adjusted", color="green")

df_inv_roul = get_norm_investment(dataset_adjusted, scaling_type=ScalingOption.ROULSTONE, conf_hash=conf_hash)
roul_imp = get_bar(df_inv_roul, "Roulsone_adjusted", color="blue")

fig.add_trace(roth_imp)
fig.add_trace(roul_imp)


# %% LCOE

dataset = "c73849526116524e476167d80f974735efba04b6456eadb2fcd85e543d991e51"
scaling_type = ScalingOption.ROULSTONE
conf_hash = "79"

result_path = get_result_path(dataset, scaling_type, conf_hash)

df_lcoe_steigerwald = pd.read_csv(result_path / "lcoe_results.csv")
df_lcoe_steigerwald.describe().T[["mean"]].round(2)

unit_doublings = find_unit_doublings(dataset=dataset_adjusted, scaling_type=scaling_type)

lcoe_improve_unit_doublings = {}

for i in unit_doublings:
    print(i)
    result_path = get_result_path(dataset_adjusted, scaling_type, conf_hash=unit_doublings[i])
    df_lcoe = pd.read_csv(result_path / "lcoe_results.csv")
    lcoe_improve_unit_doublings[i] = df_lcoe.describe().T.round(2)


for i in lcoe_improve_unit_doublings:
    lcoe_improve_unit_doublings[i]["Unit doublings"] = i

df = pd.concat(
    [
        df_lcoe_steigerwald[["BWRX-300", "UK SMR"]].describe().T,
    ]
    + list(lcoe_improve_unit_doublings.values())
)

df = df.reset_index().sort_values(by=["index","Unit doublings"])

df = df.round(0).drop(columns=["count"])
pyperclip.copy(
    df.to_latex(
        index=True,
        column_format="" + "".join(["r" for _ in df.columns]),
        caption="",
        float_format="{:.0f}".format,
        label="tab:lcoe-comparison",
    )
)

# %%


dataset_adjusted = "d70fabc6daa73dcb76730e970e24b7f9409c632b1ac4801361d425745972a55a" # 15% learning rate
scaling_type = ScalingOption.ROULSTONE



# %%
