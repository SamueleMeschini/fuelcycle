# fuel-cycle-python

OpenFC is an open-source Python model of tritium fuel cycles for fusion power plants. It
represents plant components and their connections, simulates tritium inventories over time,
and estimates the startup inventory and Tritium Breeding Ratio (TBR) needed to reach a
specified doubling time.

The model is based on the work described in the references below. It is research software;
validate results against an appropriate physical benchmark before using them for design or
safety decisions.

## Installation

The project requires Python 3.7 or newer. Create an environment and install the declared
dependencies with:

```bash
python3 -m venv .venv
source .venv/bin/activate       # Windows: .venv/Scripts/activate
python -m pip install -r requirements.txt
```

For editable installation of the package metadata, use:

```bash
python -m pip install -e .
```

## Running the reference example

The reference fuel-cycle case is in `example/fuelCycle.py`:

```bash
python example/fuelCycle.py
```

The case is intentionally long-running and opens a Matplotlib plot. Adjust `final_time`,
the timestep, or the simulation limits in that file when developing or running a short
smoke test.

## Command line

The package exposes a small command-line entry point for installation and version checks:

```bash
openfc info
openfc --version
```

## Documentation

API documentation is configured with Sphinx. Install the dependencies, then build the HTML
documentation from the repository root:

```bash
make -C docs html
```

The generated site is written to `docs/_build/html/`.

## Package layout

| Path | Purpose |
| --- | --- |
| `src/openfc/components/` | Base, plasma, fueling-system, and breeding-blanket components |
| `src/openfc/componentMap.py` | Component registration and port connections |
| `src/openfc/port.py` | Port and flow-rate representation |
| `src/openfc/simulate.py` | Inventory integration and doubling-time iteration |
| `src/openfc/tools/` | Visualization helpers |
| `example/fuelCycle.py` | Full reference simulation |
| `docs/` | Sphinx documentation source and build configuration |
| `tests/` | Test package scaffold |

## Model summary

For a generic component, the inventory derivative is modeled as:

```text
dI/dt = inflow - (1 + non_radioactive_loss) * I / residence_time
        - lambda * I + tritium_source
```

The `Plasma` and `FuelingSystem` classes specialize the generic flow behavior. The
`BreedingBlanket` produces tritium according to `N_burn * TBR`. `ComponentMap` propagates
flows through connected ports, including configured incoming and outgoing fractions.

## References

Meschini, S., Ferry, S. E., Delaporte-Mathurin, R., & Whyte, D. G. (2023). *Modeling and
analysis of the tritium fuel cycle for ARC-and STEP-class DT fusion power plants*. Nuclear
Fusion, 63(12), 126005.

Meschini, S., Delaporte-Mathurin, R., Tynan, G. R., & Ferry, S. (2025). *Impact of trapping
on tritium self-sufficiency and tritium inventories in fusion power plant fuel cycles*.
Nuclear Fusion.

## License

This project is distributed under the [Apache License 2.0](LICENSE).
