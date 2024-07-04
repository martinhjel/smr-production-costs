from abc import ABCMeta
from typing import Any, Self

import numpy as np


class Distribution(metaclass=ABCMeta):
    def __init__(self) -> None:
        pass

    def draw(self):
        pass

    def to_dict(self) -> dict[str, Any]:
        pass

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Distribution":
        pass


class Uniform(Distribution):
    def __init__(self, lower: float, upper: float, seed=None) -> None:
        self.seed = seed
        self.rng = np.random.default_rng(seed=seed)
        self.lower = lower
        self.upper = upper

    def draw(self, n_samples) -> np.array:
        return self.rng.uniform(low=self.lower, high=self.upper, size=n_samples)

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.__class__.__name__, "lower": self.lower, "upper": self.upper, "seed": self.seed}

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Self:
        return Uniform(lower=data["lower"], upper=data["upper"], seed=data["seed"])

    def __repr__(self):
        return self.__class__.__name__ + f"(lower={self.lower}, upper={self.upper})"


class Gaussian(Distribution):
    def __init__(self, mean, std, seed=None) -> None:
        self.seed = seed
        self.rng = np.random.default_rng(seed=seed)
        self.mean = mean
        self.std = std

    def draw(self, n_samples) -> np.array:
        return self.rng.normal(loc=self.mean, scale=self.std, size=n_samples)

    def to_dict(self) -> dict[str, Any]:
        return {"type": "Gaussian", "mean": self.mean, "std": self.std, "seed": self.seed}

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Self:
        return Gaussian(mean=data["mean"], std=data["std"], seed=data["seed"])

    def __repr__(self):
        return self.__class__.__name__ + f"(mean={self.mean}, std={self.std})"


class Triangular(Distribution):
    def __init__(self, left, mode, right, seed=None) -> None:
        self.seed = seed
        self.rng = np.random.default_rng(seed=seed)
        self.left = left
        self.mode = mode
        self.right = right

    def draw(self, n_samples) -> np.array:
        return self.rng.triangular(left=self.left, mode=self.mode, right=self.right, size=n_samples)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.__class__.__name__,
            "left": self.left,
            "mode": self.mode,
            "right": self.right,
            "seed": self.seed,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Self:
        return Triangular(left=data["left"], mode=data["mode"], right=data["right"], seed=data["seed"])

    def __repr__(self):
        return self.__class__.__name__ + f"(left={self.left}, mode={self.mode}, right={self.right})"


class Degenerate(Distribution):
    def __init__(self, value: int | float) -> None:
        self.value = float(value)

    def draw(self, n_samples) -> np.ndarray:
        return self.value * np.ones(shape=(n_samples,))

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.__class__.__name__, "value": self.value}

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Self:
        return Degenerate(value=data["value"])

    def __repr__(self):
        return self.__class__.__name__ + f"(vale={self.value})"
