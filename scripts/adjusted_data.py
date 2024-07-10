# %% CAPEX

import cpi

reference_2022 = [5250, 5750, 7750]

reference_2020 = []

inflation_2020_2022 = cpi.inflate(1, 2020, 2022)
for c in reference_2022:
    reference_2020.append(c / inflation_2020_2022)

bwr_reference_cap = 935
pwr_reference_cap = 1117

bwr_reference_cost = []
pwr_reference_cost = []
for c in reference_2020:
    bwr_reference_cost.append(bwr_reference_cap * c)
    pwr_reference_cost.append(pwr_reference_cap * c)

print("BWR:", bwr_reference_cost)
print("PWR:", pwr_reference_cost)

# %% O&M and fuel cost

fuel_cost_2022 = [10, 11, 12.1] # USD/MWh
fixed_om_2022 = [118, 136, 216] # USD/kW-yr
var_om_2022 = [2.2, 2.6, 2.8] # USD/MWh

fuel_cost_2020 = []
fixed_om_2020 = []
var_om_2020 = []
for i, _ in enumerate(fuel_cost_2022):
    fuel_cost_2020.append(fuel_cost_2022[i] / inflation_2020_2022)
    fixed_om_2020.append(fixed_om_2022[i] / inflation_2020_2022)
    var_om_2020.append(var_om_2022[i] / inflation_2020_2022)

print("fuel :", [f"{i:.2f}" for i in fuel_cost_2020])
print("fixed_om :", [f"{i*1e3:.2f}" for i in fixed_om_2020]) # USD/MW-yr
print("var_om :", [f"{i:.2f}" for i in var_om_2020])
# %%
