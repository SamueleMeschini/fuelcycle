# fuel-cycle-python

An exploratory Python model for high-level tritium fuel-cycle analysis in fusion systems.
The repository represents a fuel cycle as connected components and ports, advances the
tritium inventory of each component in time, and includes utilities for tritium transport
and mass-transfer calculations.

## What is included

- `Component`, `Port`, and `ComponentMap` model inventories, flows, and connections.
- `FuelingSystem`, `Plasma`, and `BreedingBlanket` provide fuel-cycle-specific component
  behavior.
- `Simulate` integrates the inventory equations with forward Euler time stepping and an
  adaptive timestep. Its `run()` method can also adjust startup inventory and the breeding
  blanket tritium breeding ratio (TBR) for the configured targets.
- `tools/` contains heat/mass-transfer correlations, extractor correlations, and helpers
  for liquid-metal and molten-salt systems.
- `test.ipynb` is an exploratory notebook.

This is research code and is not currently packaged as an installable Python module.
Results should be checked against an appropriate physical benchmark before being used for
design or safety decisions.

## Requirements

Use Python 3 with the following third-party packages:

- NumPy
- Matplotlib
- NetworkX

Create an environment and install the dependencies with:

```bash
python3 -m venv .venv
source .venv/bin/activate       # On Windows: .venv\\Scripts\\activate
python -m pip install numpy matplotlib networkx
```

Run commands from the repository root because the scripts use local, top-level imports.

## Running the examples

The full reference case is in `fuelCycle.py`:

```bash
python fuelCycle.py
```

It builds a cycle containing the fueling system, plasma, breeding blanket, first wall,
divertor, intermediate fuel cycle, thermal energy storage, heat exchanger, and detritiation
system. It prints the connected map and inventory information and opens plots for the
component map and simulation results. The reference case is intentionally long-running;
reduce `final_time` or use a smaller test case when iterating on the model.

`example_simulation.py` contains a smaller cycle. It uses an older `Simulate` call, so
update its simulation setup to the current API and call the generic integrator directly:

```python
simulation = Simulate(
    dt=0.1,
    final_time=1e5,
    I_reserve=0,
    component_map=component_map,
)
t, y = simulation.forward_euler()
```

Then run it with:

```bash
python example_simulation.py
```

The example displays the inventory history. `run()` is reserved for the full fuel-cycle
workflow described below. For a non-interactive environment, remove or replace the
`plt.show()` call in `tools/utils.py`.

## Minimal model example

```python
from component import Component
from componentMap import ComponentMap
from simulate import Simulate

source = Component("Fueling System", residence_time=3600, initial_inventory=1.0)
sink = Component("Sink", residence_time=3600)

source_out = source.add_output_port("out")
sink_in = sink.add_input_port("in")

cycle = ComponentMap()
cycle.add_component(source)
cycle.add_component(sink)
cycle.connect_ports(source, source_out, sink, sink_in)

simulation = Simulate(
    dt=1.0,
    final_time=3600,
    I_reserve=0,
    component_map=cycle,
)
time, inventories = simulation.forward_euler()
```

`inventories` contains one inventory vector per time step, in the same order as
`cycle.components`. The current `Simulate` implementation requires a component named
`Fueling System` during initialization. Use `simulation.run()` for the full fuel-cycle
workflow; it additionally expects a component named `BB` if TBR adjustment is needed.

## Model overview

For a generic `Component`, the inventory derivative is approximately:

```text
dI/dt = inflow - (1 + non_radioactive_loss) * I / residence_time
        - lambda * I + tritium_source
```

where `I` is the tritium inventory and `lambda` is the tritium decay constant defined in
`component.py`. Connections determine flow rates from component outflow and the receiving
port's `incoming_fraction`. `Plasma` and `FuelingSystem` override the generic inflow/outflow
relations, while `BreedingBlanket` sets its source to `N_burn * TBR`.

## Repository layout

| Path | Purpose |
| --- | --- |
| `component.py` | Base inventory component |
| `port.py` | Component ports and flow rates |
| `componentMap.py` | Component registration and connections |
| `fuelingSystem.py` | Fueling-system behavior |
| `plasma.py` | Plasma burn and exhaust behavior |
| `breedingBlanket.py` | Tritium breeding behavior |
| `simulate.py` | Time integration and fuel-cycle iteration |
| `fuelCycle.py` | Full reference fuel-cycle case |
| `example_simulation.py` | Small illustrative case |
| `tools/` | Transport, extractor, and correlation utilities |
| `test.ipynb` | Exploratory analysis |

## Development status

The repository does not currently include automated tests, dependency metadata, or a
stable package API. Contributions should include a small reproducible example or validation
case when changing model behavior.

## License

This project is released under the [MIT License](LICENSE).
