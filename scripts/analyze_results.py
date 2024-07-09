#%%
from pathlib import Path
import pyperclip
import pandas as pd
import plotly.graph_objects as go

from scripts.case_studies import get_project_data
from smr_mcs.config import ScalingOption


def get_result_path(dataset: str, scaling_type: ScalingOption, conf_hash: str):
    results_path = Path.cwd() / f"results/{dataset}/{scaling_type.value}"
    results = [i for i in results_path.glob("*")]

    for r in results:
        if conf_hash == r.name[: len(conf_hash)]:
            return r

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
    y=df_inv_manuf.columns, x=df_inv_manuf.iloc[0, :], mode="markers", marker=dict(color="red", size=10), name="Manufacturer"
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


#%%

df_npv = pd.read_csv(result_path / "npv_results.csv")
df_npv.describe().T


#%%

dataset = "1e92538df43ed27d6716e72185cab99ea6cb86a6e40fc1a2406765025052fdcf"
conf_hash = "9c"
df_inv_roth = get_norm_investment(dataset, scaling_type=ScalingOption.ROTHWELL, conf_hash=conf_hash)
roth_imp = get_bar(df_inv_roth, "Rothwell_adjusted", color="green")

df_inv_roul = get_norm_investment(dataset, scaling_type=ScalingOption.ROULSTONE, conf_hash=conf_hash)
roul_imp = get_bar(df_inv_roul, "Roulsone_adjusted", color="blue")

fig.add_trace(roth_imp)
fig.add_trace(roul_imp)


#%% LCOE

dataset = "c73849526116524e476167d80f974735efba04b6456eadb2fcd85e543d991e51"
scaling_type = ScalingOption.ROULSTONE
conf_hash = "79"

result_path = get_result_path(dataset, scaling_type, conf_hash)
# df_projects = get_project_data()
df_lcoe_steigerwald = pd.read_csv(result_path / "lcoe_results.csv")

df_lcoe_steigerwald.describe().T[["mean"]].round(2)


dataset_adjusted = "1e92538df43ed27d6716e72185cab99ea6cb86a6e40fc1a2406765025052fdcf"
unit_doublings = {
    1: "9c",
    2: "4f6",
    3: "ecc",
    4: "8d",
    5: "c0"
    
}
lcoe_improve_unit_doublings = {}

for i in unit_doublings:
    print(i)
    result_path = get_result_path(dataset_adjusted, scaling_type, conf_hash=unit_doublings[i])
    df_lcoe = pd.read_csv(result_path / "lcoe_results.csv")
    lcoe_improve_unit_doublings[i] = df_lcoe.describe().T.round(2)


for i in lcoe_improve_unit_doublings:
    lcoe_improve_unit_doublings[i]["Unit doublings"] = i
    
df = pd.concat([
    df_lcoe_steigerwald[["BWRX-300", "UK SMR"]].describe().T,
] + list(lcoe_improve_unit_doublings.values()))

df = df.round(2).drop(columns=["count"])
pyperclip.copy(
    df.to_latex(
        index=True,
        column_format="" + "".join(["r" for _ in df.columns]),
        caption="",
        float_format="{:.1f}".format,
        label="tab:lcoe-comparison",
    )
)