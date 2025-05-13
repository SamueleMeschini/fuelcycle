import numpy as np
from components.chemical_species import ChemicalSpecies


kb = 1.380648e-23
R = 8.314  # J/molK
NA = R/kb

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
        self.valve = 1
        self.plot_counter = 0
        self.total_mass_inventory = 0
        self.total_throughput_inventory = 0
        self.active = True
        self.regenerating = False
        self.stand_by = False
        self.regen_time_left = 0
        self.saturation = 0
        self.total_mass_inventory_evolution = [0]
        self.total_throughput_inventory_evolution = [0]
        self.species_mass_inventory = {name: 0 for name in CS.species.keys()}
        self.species_mass_inventory_evolution = {name: [0] for name in CS.species.keys()}
        self.species_throughput_inventory = {name: 0 for name in CS.species.keys()}
        self.species_throughput_inventory_evolution = {name: [0] for name in CS.species.keys()}
        self.species_inventory_fraction = {name: 0 for name in CS.species.keys()}
        self.species_inventory_fraction_evolution = {name: [0] for name in CS.species.keys()}
        self.hydrogen_throughput_inventory = 0
        self.hydrogen_throughput_inventory_evolution = [0]
        self.species_pumping_speed = {specie.name: specie.pumping_speed for specie in CS.species.values()}
        self.time_evolution = []
        self.species_particles_flow_rate = {specie.name: 0 for specie in CS.species.values()}
        self.species_throughput = {specie.name: 0 for specie in CS.species.values()}
        self.species_mass_flow_rate = {specie.name: 0 for specie in CS.species.values()}
        self.species_particles_inflow = {specie.name: 0 for specie in CS.species.values()}
        self.species_throughput_inflow = {specie.name: 0 for specie in CS.species.values()}
        self.species_mass_flow_rate_inflow = {specie.name: 0 for specie in CS.species.values()}

    def update_active_pump(self, CS, time, dt):
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
        self.time_evolution.append(time)
        

        self.total_throughput_inventory += self.total_throughput_inflow*dt
        self.total_throughput_inventory_evolution.append(self.total_throughput_inventory)
        for specie in CS.species.values():
            self.species_throughput_inventory[specie.name] += self.species_throughput_inflow[specie.name]*dt
            self.species_throughput_inventory_evolution[specie.name].append(self.species_throughput_inventory[specie.name])
            self.species_mass_inventory[specie.name] += self.species_mass_flow_rate_inflow[specie.name]*dt
            self.species_mass_inventory_evolution[specie.name].append(self.species_mass_inventory[specie.name])
            self.total_mass_inventory += self.species_mass_inventory[specie.name]
        self.hydrogen_throughput_inventory = self.species_throughput_inventory["Tritium"] + self.species_throughput_inventory["Deuterium"]
        self.hydrogen_throughput_inventory_evolution.append(self.hydrogen_throughput_inventory)
        self.saturation = self.total_throughput_inventory/self.max_capacity
        self.total_mass_inventory_evolution.append(self.total_mass_inventory)

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

    def update_valve(self, tritium_inflow, CS):
        self.valve = tritium_inflow/self.species_mass_flow_rate["Tritium"]
        if self.valve>1:
            self.valve = 1

    def get_limiting_factor(self, VP, dt):
        limit = min(dt, ((0.95*self.max_capacity-self.total_throughput_inventory)/self.total_throughput_inflow), (self.max_hydrogen_capacity - self.hydrogen_throughput_inventory) / (self.species_throughput_inflow["Tritium"] + self.species_throughput_inflow["Deuterium"]))
        if limit == dt:
            if self.valve == 1:
                self.limiting_factor = "Pump throughput"
            else:
                self.limiting_factor = "Plasma limitation"
        if limit == (0.95*self.max_capacity-self.total_throughput_inventory)/self.total_throughput_inflow:
            self.valve = self.valve*(0.95*self.max_capacity-self.total_throughput_inventory)/self.total_throughput_inflow/dt
            self.limiting_factor = "Max capacity"
            VP.pump_deactivation(self)
        if limit == (self.max_hydrogen_capacity - self.hydrogen_throughput_inventory) / (self.species_throughput_inflow["Tritium"] + self.species_throughput_inflow["Deuterium"]):
            self.valve =self.valve*(self.max_hydrogen_capacity - self.hydrogen_throughput_inventory) / (self.species_throughput_inflow["Tritium"] + self.species_throughput_inflow["Deuterium"])/dt
            self.limiting_factor = "Hydrogen explosion risk"
            VP.pump_deactivation(self)
            #print(f"hydrogen limit reached, {self.hydrogen_throughput_inventory + dt*(self.species_throughput_inflow["Tritium"] + self.species_throughput_inflow["Deuterium"])} by {self.name}")
        
    #def get_regenration_valve(self):
        #self.regeneration_valve = self.temporary_total_inventory/self.max_capacity

    def get_desorption_speed(self, kd, dt):
        #self.desorption_speed = self.max_capacity/self.regeneration_time / (1 + np.exp(-kd * (self.saturation - 0.5)))
        self.desorption_speed = self.max_capacity/self.regeneration_time*self.saturation**2/((self.saturation**2)+(1-self.saturation)**2)
        if self.total_throughput_inventory - self.desorption_speed*dt <0:
            self.desorption_speed = self.total_throughput_inventory/dt
        #print(f"Desorption speed of {self.name} = {self.desorption_speed}, with saturation = {self.saturation}")

    def get_gas_fraction(self, CS):
         for specie in CS.species.values():
            self.species_inventory_fraction[specie.name] = self.species_throughput_inventory[specie.name]/self.total_throughput_inventory
            self.species_inventory_fraction_evolution[specie.name].append(self.species_inventory_fraction[specie.name])

    
    def update_regenerating_pump(self, CS, time, dt):
        self.get_desorption_speed(1, dt)
        #for specie in CS.species.values():
            #print(specie.name, self.species_inventory_fraction[specie.name])
        self.get_gas_fraction(CS)
        #for specie in CS.species.values():
            #print(specie.name, self.species_inventory_fraction[specie.name])
    
        if self.time_evolution == [] and time != 0:
            self.time_evolution.append(time - dt)
        self.time_evolution.append(time)
        #self.total_throughput_inventory -= self.desorption_speed*dt
        #self.total_throughput_inventory_evolution.append(self.total_throughput_inventory)
        self.total_mass_inventory = 0
        self.total_throughput_inventory = 0
        for specie in CS.species.values():
            self.species_throughput_inventory[specie.name] -= self.desorption_speed*self.species_inventory_fraction[specie.name]*dt #Pa*m^3
            self.species_throughput_inventory_evolution[specie.name].append(self.species_throughput_inventory[specie.name])
            self.species_mass_inventory[specie.name] = self.species_throughput_inventory[specie.name] * CS.species[specie.name].molecular_mass/R/273.15/1e3
            self.species_mass_inventory_evolution[specie.name].append(self.species_mass_inventory[specie.name])
            self.total_mass_inventory += self.species_mass_inventory[specie.name]
            self.total_throughput_inventory += self.species_throughput_inventory[specie.name]
        self.hydrogen_throughput_inventory = self.species_throughput_inventory["Tritium"] + self.species_throughput_inventory["Deuterium"]
        self.hydrogen_throughput_inventory_evolution.append(self.hydrogen_throughput_inventory)
        self.saturation = self.total_throughput_inventory/self.max_capacity
        self.total_mass_inventory_evolution.append(self.total_mass_inventory)
        self.total_throughput_inventory_evolution.append(self.total_throughput_inventory)
        #for specie in CS.species.values():
            #print(specie.name, self.species_inventory_fraction[specie.name], self.desorption_speed*self.species_inventory_fraction[specie.name]*dt,  self.species_mass_inventory[specie.name]/self.total_mass_inventory,self.species_mass_inventory[specie.name],  time)
        #print("\n\n")

    def get_pump_particles_flow_rate(self, CS):
        for specie in CS.species.values():
            self.species_particles_flow_rate[specie.name]=specie.density*self.species_pumping_speed[specie.name]

    def get_pump_throughput(self, CS):
        for specie in CS.species.values():
            self.species_throughput[specie.name]=specie.partial_pressure*self.species_pumping_speed[specie.name]

    def get_pump_mass_flow_rate(self, CS):
        self.get_pump_particles_flow_rate(CS)
        for specie in CS.species.values():
            self.species_mass_flow_rate[specie.name]=self.species_particles_flow_rate[specie.name]/ NA * specie.molecular_mass / 1e3
  



    def get_pump_particles_inflow(self, CS):
        self.total_particles_inflow = 0
        for specie in CS.species.values():
            self.species_particles_inflow[specie.name]=specie.density*self.species_pumping_speed[specie.name]*self.valve
            self.total_particles_inflow += self.species_particles_inflow[specie.name]
    
    def get_pump_throughput_inflow(self, CS):
        self.total_throughput_inflow = 0
        for specie in CS.species.values():
            self.species_throughput_inflow[specie.name]=specie.partial_pressure*self.species_pumping_speed[specie.name]*self.valve
            self.total_throughput_inflow += self.species_throughput_inflow[specie.name]

    def get_pump_mass_flow_rate_inflow(self, CS):
        self.get_pump_particles_inflow(CS)
        self.total_mass_flow_rate_inflow = 0
        for specie in CS.species.values():
            self.species_mass_flow_rate_inflow[specie.name]=self.species_particles_inflow[specie.name]/NA*specie.molecular_mass/1e3
            self.total_mass_flow_rate_inflow += self.species_throughput_inflow[specie.name]
        
    def update_pumping_speed(self, CS):
        for specie in CS.species.values():
            specie.get_dynamic_pumping_speed(self.saturation)
            self.species_pumping_speed[specie.name] = specie.dynamic_pumping_speed