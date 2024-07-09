from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Self

import yaml

from smr_mcs.distributions import Degenerate, Distribution, Gaussian, Triangular, Uniform  # noqa
from smr_mcs.project import create_distribution


class ScalingOption(Enum):
    MANUFACTURER = "manufacturer"
    ROULSTONE = "roulstone"
    ROTHWELL = "rothwell"


@dataclass
class SimulationConfig:
    """
    A configuration class for Monte Carlo simulation parameters.

    :param n: The number of Monte Carlo simulation runs.
    :param wacc: The distribution function to use for generating WACC values.
    :param electricity_price: The distribution function to use for generating electricity price values.
    :param scaling: The distribution function to use for generating scaling factor values.
    :param opt_scaling: The scaling option to use for calculating investment costs.
    :param unit_doubling: How many times doubling of unit production has occured.
    """

    n: int
    wacc: Distribution
    electricity_price: Distribution
    scaling: Distribution
    opt_scaling: ScalingOption
    unit_doubling: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "n": self.n,
            "wacc": self.wacc.to_dict(),
            "electricity_price": self.electricity_price.to_dict(),
            "scaling": self.scaling.to_dict(),
            "opt_scaling": self.opt_scaling.value,
            "unit_doubling": self.unit_doubling,
        }

    def __str__(self):
        return self.__repr__()

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Self:
        return SimulationConfig(
            n=data["n"],
            wacc=create_distribution(data["wacc"]),
            electricity_price=create_distribution(data["electricity_price"]),
            scaling=create_distribution(data["scaling"]),
            opt_scaling=ScalingOption(data["opt_scaling"]),
            unit_doubling=data["unit_doubling"],
        )

    @staticmethod
    def from_yaml(yaml_file: Path) -> Self:
        with open(yaml_file, "r") as file:
            data = yaml.safe_load(file)
        return SimulationConfig.from_dict(data=data)

    def __eq__(self, other):
        if isinstance(other, SimulationConfig):
            return (
                self.n == other.n
                and self.wacc == other.wacc
                and self.electricity_price == other.electricity_price
                and self.scaling == other.scaling
                and self.opt_scaling == other.opt_scaling
                and self.unit_doubling == other.unit_doubling
            )
        return False


if __name__ == "__main__":
    # Example usage
    config = SimulationConfig(
        n=int(1e6),
        electricity_price=Gaussian(mean=70, std=30),
        wacc=Triangular(left=0.04, mode=0.06, right=0.12),
        scaling=Uniform(lower=0.20, upper=0.75),
        opt_scaling=ScalingOption.ROULSTONE,  # or ScalingOption['ROULSTONE']
        unit_doubling=1
    )

    dct = config.to_dict()

    config2 = SimulationConfig.from_dict(dct)

    print(config == config2)