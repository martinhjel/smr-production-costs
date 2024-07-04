# %%
import configparser
from pathlib import Path

import pandas as pd
from entsoe import EntsoePandasClient, EntsoeRawClient
from entsoe.parsers import _extract_timeseries, _parse_price_timeseries

# %%


def parse_prices(xml_text):
    """
    Parameters
    ----------
    xml_text : str

    Returns
    -------
    pd.Series
    """
    series = {"15min": [], "30min": [], "60min": []}
    for soup in _extract_timeseries(xml_text):
        soup_series = _parse_price_timeseries(soup)
        series[soup_series.index.freqstr].append(soup_series)

    for freq, freq_series in series.items():
        if len(freq_series) > 0:
            series[freq] = pd.concat(freq_series).sort_index()
    return series["60min"].to_frame()


# %%
pd.set_option("plotting.backend", "plotly")

# %%
config_path = Path.cwd() / "config.ini"
config_path.exists()
# %%
config = configparser.ConfigParser()
config.read(config_path)
# %%
web_token = config["entsoe"]["security_token"]
# %%
client = EntsoePandasClient(api_key=web_token)
raw_client = EntsoeRawClient(api_key=web_token)
# %%
start = pd.Timestamp("2022-12-31T22:00Z")
end = pd.Timestamp("2024-01-01T02:00Z")
country_code = "SE"

df_gen = client.query_generation(country_code, start=start, end=end)

# %% Returns local time
price_area_code = "SE_3"
df_load = client.query_load(country_code=price_area_code, start=start, end=end)

# %% Returns utc time
prices = raw_client.query_day_ahead_prices(country_code=price_area_code, start=start, end=end)
df_prices = parse_prices(prices)
# %% Convert to local time and merge

df_gen.index = df_gen.index.tz_convert("Europe/Stockholm")
df_prices.index = df_prices.index.tz_convert("Europe/Stockholm")
df_load.index = df_load.index.tz_convert("Europe/Oslo")

df_prices = df_prices.rename(columns={0: "SpotPrice"})

df = pd.merge(df_gen, df_prices, how="inner", left_index=True, right_index=True)
df = pd.merge(df, df_load, how="inner", left_index=True, right_index=True)
df.index = df.index.tz_convert("Europe/Oslo")


#%%
df = df[df.index.year==2023]

#%%

weighted_price = (df["SpotPrice"] * df["Actual Load"]).sum() / df["Actual Load"].sum()
non_weigted_price = df["SpotPrice"].mean()

print(f"Weighted price     {weighted_price:.2f}")
print(f"Non-weighted price {non_weigted_price:.2f}")

data = {"Capture price": [], "Weighted value factor": [], "Non-weighted value factor": []}
for col in df.columns:
    capture_price = (df[col] * df["SpotPrice"]).sum() / df[col].sum()

    data["Capture price"].append(capture_price)
    data["Weighted value factor"].append(capture_price / weighted_price)
    data["Non-weighted value factor"].append(capture_price / non_weigted_price)

pd.DataFrame(data=data,index=df.columns)




# %%
