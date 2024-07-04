from dataclasses import dataclass
from enum import Enum
from typing import Any, Self

from smr_mcs.distributions import Degenerate, Distribution, Gaussian, Triangular, Uniform  # noqa


class ScalingOption(Enum):
    MANUFACTURER = "manufacturer"
    ROULSTONE = "roulstone"
    ROTHWELL = "rothwell"
    UNIFORM = "uniform"


@dataclass
class SimulationConfig:
    """
    A configuration class for Monte Carlo simulation parameters.

    :param n: The number of Monte Carlo simulation runs.
    :param wacc: The distribution function to use for generating WACC values.
    :param electricity_price: The distribution function to use for generating electricity price values.
    :param scaling: The distribution function to use for generating scaling factor values.
    :param opt_scaling: The scaling option to use for calculating investment costs.
    """

    n: int
    wacc: Distribution
    electricity_price: Distribution
    scaling: Distribution
    opt_scaling: ScalingOption

    def to_dict(self) -> dict[str, Any]:
        return {
            "n": self.n,
            "wacc": self.wacc.to_dict(),
            "electricity_price": self.electricity_price.to_dict(),
            "scaling": self.scaling.to_dict(),
            "opt_scaling": self.opt_scaling.value,
        }

    def __str__(self):
        return self.__repr__

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Self:
        return SimulationConfig(
            n=data["n"],
            wacc=globals()[dct["wacc"]["type"]].from_dict(data["wacc"]),
            electricity_price=globals()[dct["electricity_price"]["type"]].from_dict(data["electricity_price"]),
            scaling=globals()[dct["scaling"]["type"]].from_dict(data["scaling"]),
            opt_scaling=ScalingOption(data["opt_scaling"]),
        )


if __name__ == "__main__":
    # Example usage
    config = SimulationConfig(
        n=int(1e6),
        electricity_price=Gaussian(mean=70, std=30),
        wacc=Triangular(left=0.04, mode=0.06, right=0.12),
        scaling=Uniform(lower=0.20, upper=0.75),
        opt_scaling=ScalingOption.ROULSTONE,  # or ScalingOption['ROULSTONE']
    )

    dct = config.to_dict()

    SimulationConfig.from_dict(dct)
