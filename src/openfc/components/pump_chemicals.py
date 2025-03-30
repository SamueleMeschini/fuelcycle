import numpy as np
from chemical_species import ChemicalSpecies

class Pump:
    """
    A class to represent a pump in a cryopump system.

    Attributes:
    -----------
    name : str
        The name of the pump.
    max_capacity : float
        The maximum capacity of the pump.
    regeneration_time : float
        The regeneration time of the pump.
    max_hydrogen_capacity : float
        The maximum hydrogen capacity of the pump.
    plot_counter : int
        A counter for the number of plots generated.
    total_inventory : float
        The total inventory of the pump.
    species_inventories : dict
        A dictionary to store the inventory for each species.
    active : bool
        The status of the pump (active/inactive).
    regenerating : bool
        The status of the pump (regenerating/not regenerating).
    stand_by : bool
        The status of the pump (stand-by/not stand-by).
    regen_time_left : float
        The remaining regeneration time for the pump.
    total_inventory_evolution : list
        A list to store the evolution of the total inventory.
    species_inventory_evolution : dict
        A dictionary to store the evolution of the inventory for each species.
    species_throughput_inventories : dict
        A dictionary to store the throughput inventory for each species.
    species_throughput_inventory_evolution : dict
        A dictionary to store the evolution of the throughput inventory for each species.
    hydrogen_throughput_inventory : list
        A list to store the hydrogen throughput inventory.
    hydrogen_throughput_inventory_evolution : list
        A list to store the evolution of the hydrogen throughput inventory.
    time_evolution : list
        A list to store the time evolution.
    """

    def __init__(self, id, CS, max_capacity, regeneration_time, max_hydrogen_capacity):
        """
        Constructs all the necessary attributes for the pump object.

        Parameters:
        -----------
        id : int
            The ID of the pump.
        CS : ChemicalSpecies
            The chemical species involved in the cryopump system.
        max_capacity : float
            The maximum capacity of the pump.
        regeneration_time : float
            The regeneration time of the pump.
        max_hydrogen_capacity : float
            The maximum hydrogen capacity of the pump.
        """
        self.name = f"Pump n. {id}"
        self.max_capacity = max_capacity
        self.regeneration_time = regeneration_time
        self.max_hydrogen_capacity = max_hydrogen_capacity
        self.plot_counter = 0
        self.total_inventory = 0
        self.species_inventories = {name: 0 for name in CS.species.keys()}
        self.active = True
        self.regenerating = False
        self.stand_by = False
        self.regen_time_left = 0
        self.total_inventory_evolution = [0]
        self.species_inventory_evolution = {name: [0] for name in CS.species.keys()}
        self.species_throughput_inventories = {name: 0 for name in CS.species.keys()}
        self.species_throughput_inventory_evolution = {name: [0] for name in CS.species.keys()}
        self.hydrogen_throughput_inventory = [0]
        self.hydrogen_throughput_inventory_evolution = [0]
        self.time_evolution = []

    def update_inventory(self, intake, CS, time, dt):
        """
        Updates the inventory of the pump for each species.

        Parameters:
        -----------
        intake : float
            The intake value for the pump.
        CS : ChemicalSpecies
            The chemical species involved in the cryopump system.
        time : float
            The current time.
        dt : float
            The time step for the update.
        """
        if self.time_evolution == [] and time != 0:
            self.time_evolution.append(time - dt)
        self.total_inventory += intake  # Pa*m^3
        self.total_inventory_evolution.append(self.total_inventory)
        self.time_evolution.append(time)
        CS.get_species_mass_intake(intake)
        for specie in CS.species.values():
            self.species_inventories[specie.name] += specie.mass_intake
            self.species_inventory_evolution[specie.name].append(self.species_inventories[specie.name])
            self.species_throughput_inventories[specie.name] += intake * specie.throughput_intake_coefficient
            self.species_throughput_inventory_evolution[specie.name].append(self.species_throughput_inventories[specie.name])
        self.hydrogen_throughput_inventory = self.species_throughput_inventories["Tritium"] + self.species_throughput_inventories["Deuterium"]
        self.hydrogen_throughput_inventory_evolution.append(self.hydrogen_throughput_inventory)

    def activation(self):
        """Activates the pump and increments the plot counter."""
        self.regenerating = False
        self.active = True
        self.plot_counter += 1

    def deactivation(self):
        """Deactivates the pump and sets it to stand-by and regenerating status."""
        self.stand_by = True
        self.active = False
        self.regenerating = True
        self.regen_time_left = self.regeneration_time