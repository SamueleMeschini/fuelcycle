"""Smoke tests for the public package surface."""

import openfc


def test_public_classes_are_exported() -> None:
    expected = {
        "BreedingBlanket",
        "Component",
        "ComponentMap",
        "FuelingSystem",
        "Plasma",
        "Port",
        "Simulate",
    }

    assert expected.issubset(set(openfc.__all__))
    assert openfc.__version__


def test_snake_case_imports_point_to_public_classes() -> None:
    from openfc.component_map import ComponentMap
    from openfc.components.breeding_blanket import BreedingBlanket
    from openfc.components.fueling_system import FuelingSystem

    assert ComponentMap is openfc.ComponentMap
    assert BreedingBlanket is openfc.BreedingBlanket
    assert FuelingSystem is openfc.FuelingSystem
