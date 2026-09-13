"""Public package interface for OpenFC.

The implementation modules remain available for detailed use, while the most
common classes are re-exported here to provide a stable, concise import path.
"""

from .component_map import ComponentMap
from .port import Port
from .simulate import Simulate
from .components import BreedingBlanket, Component, FuelingSystem, Plasma

__all__ = [
    "BreedingBlanket",
    "Component",
    "ComponentMap",
    "FuelingSystem",
    "Plasma",
    "Port",
    "Simulate",
    "__version__",
]

__version__ = "0.0.1"
