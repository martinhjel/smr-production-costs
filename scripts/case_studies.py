from pathlib import Path

import pandas as pd


def get_project_data():
    data_path = Path.cwd() / "data/project_data_raw.csv"

    if data_path.exists():
        return pd.read_csv(data_path, sep=";")
    else:
        project_data_path = "https://raw.githubusercontent.com/weibezahn/smr-mcs/master/_input/project_data.csv"
        df = pd.read_csv(project_data_path, sep=";")
        df.to_csv(data_path, sep=";", index=False)

        return df
