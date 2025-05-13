import numpy as np
from components.component import Component
import time as tp
from matplotlib import pyplot as plt
from components.chemical_species import ChemicalSpecies
from components.chemical_species import Element
from components.pump_chemicals import Pump

kb = 1.380648e-23
R = 8.314  # J/molK
NA = R/kb

class CryopumpSystem(Component):
    """
    A class to represent a cryopump system.

    Attributes:
    -----------
    name : str
        The name of the cryopump system.
    max_capacity : float
        The maximum capacity of the cryopump system.
    max_hydrogen_capacity : float
        The maximum hydrogen capacity of the cryopump system.
    pumping_speed : float
        The pumping speed of the cryopump system.
    regeneration_time : float
        The regeneration time of the cryopump system.
    TBE : float
        Tritium burning efficiency.
    LAMBDA : float
        Radioactive loss coefficient.
    non_radioactive_loss : float, optional
        The non-radioactive loss (default is 1e-4).
    divertor_pressure : float, optional
        The divertor pressure (default is 1).
    """

    def __init__(self, name, max_capacity, max_hydrogen_capacity, pumping_speed, regeneration_time, CS, LAMBDA, non_radioactive_loss=1e-4, TBE=0.02, divertor_pressure=1, **kwargs):
        """
        Constructs all the necessary attributes for the cryopump system object.

        Parameters:
        -----------
        name : str
            The name of the cryopump system.
        max_capacity : float
            The maximum capacity of the cryopump system.
        max_hydrogen_capacity : float
            The maximum hydrogen capacity of the cryopump system.
        pumping_speed : float
            The pumping speed of the cryopump system.
        regeneration_time : float
            The regeneration time of the cryopump system.
        CS : ChemicalSpecies
            The chemical species involved in the cryopump system.
        LAMBDA : float
            Radioactive loss coefficient.
        non_radioactive_loss : float, optional
            The non-radioactive loss (default is 1e-4).
        TBE : float, optional
            Tritium burning efficiency (default is 0.02).
        divertor_pressure : float, optional
            The divertor pressure (default is 1).
        """
        super().__init__(name, residence_time=1, **kwargs)

        self.TBE = TBE
        self.LAMBDA = LAMBDA
        self.non_radioactive_loss = non_radioactive_loss
        self.name = name
        self.pumping_speed = pumping_speed  
        self.regeneration_time = regeneration_time  
        self.max_capacity = max_capacity
        self.max_hydrogen_capacity = max_hydrogen_capacity
        
        self.pumps = [] 
        self.regenerating_pumps = []  
        self.active_pumps = []
        self.stand_by_pumps = []
        self.outflow = []
        self.inflow = []
        self.tritium_inventory = 0

    def add_pump(self, CS):
        """
        Adds a new active pump to the cryopump system.

        Parameters:
        -----------
        CS : ChemicalSpecies
            The chemical species involved in the cryopump system.
        """
        pump = Pump(len(self.pumps) + 1, CS, self.max_capacity, self.regeneration_time, self.max_hydrogen_capacity)
        self.pumps.append(pump)
        self.active_pumps.append(pump)

    def update_pumps(self, a, dt, time, CS):
    
        """
        Updates the existing pumps and checks if new ones are needed.

        Parameters:
        -----------
        a : float
            A parameter for the update process.
        dt : float
            The time step for the update.
        time : float
            The current time.
        CS : ChemicalSpecies
            The chemical species involved in the cryopump system.
        """
        CS.get_intake_coefficients()
        total_tritium_inflow = self.get_inflow() * dt  # tritium kg
        mass_tritium_outflow = 0  # Total outflow
        for pump in self.pumps:
            CS.get_throughput_inflow(total_tritium_inflow)  # Pa*m^3
            if pump.active:
                if pump not in self.active_pumps:
                    self.active_pumps.append(pump)
                intake = min(
                    CS.total_throughput * dt,
                    CS.total_throughput_inflow,
                    pump.max_capacity - pump.total_inventory,
                    (pump.max_hydrogen_capacity - pump.hydrogen_throughput_inventory) / CS.hydrogen_throughput_intake_coefficient
                )
                if pump.total_inventory > 0 and intake < 1e-12:
                    pump.temporary_total_inventory = pump.total_inventory
                    pump.active = False
                    pump.regenerating = True
                    self.regenerating_pumps.append(pump)
                    self.active_pumps.remove(pump)
                    continue
                pump.update_inventory(intake, CS, time, dt)
                total_tritium_inflow -= CS.species["Tritium"].mass_intake
                if pump.total_inventory >= pump.max_capacity or pump.hydrogen_throughput_inventory >= pump.max_hydrogen_capacity:
                    pump.temporary_total_inventory = pump.total_inventory
                    self.pump_deactivation(pump)

        for pump in self.pumps:
            if pump.regenerating == True:
                if pump.stand_by == True:
                    pass
                else:
                    intake = -min(pump.temporary_total_inventory/pump.regeneration_time*dt, pump.total_inventory)
                    pump.update_inventory(intake, CS, time, dt)
                    mass_tritium_outflow -= CS.species["Tritium"].mass_intake #positive number, kg
                    pump.regen_time_left -= dt
                    if pump.total_inventory <= 0:
                        self.pump_activation(pump)

        while total_tritium_inflow > 1e-12:
            self.add_pump(CS)
            CS.get_throughput_inflow(total_tritium_inflow)
            intake = min(CS.total_throughput * dt, CS.total_throughput_inflow)
            self.pumps[-1].update_inventory(intake, CS, time, dt)
            total_tritium_inflow -= CS.species["Tritium"].mass_intake
            self.print_new_pump(time, mass_tritium_outflow, CS, intake, dt)

        self.switch_on_stand_by_pumps()
        self.outflow.append(mass_tritium_outflow / dt * (1 - CS.species["Tritium"].decay_constant))
        self.inflow.append(self.get_inflow())

    def update_inventory(self, a, dt, time, CS):
        """
        Updates the inventory of the cryopump system.

        Parameters:
        -----------
        a : float
            A parameter for the update process.
        dt : float
            The time step for the update.
        time : float
            The current time.
        CS : ChemicalSpecies
            The chemical species involved in the cryopump system.

        Returns:
        --------
        float
            The total tritium inventory of all pumps.
        """
        self.update_pumps(a, dt, time, CS)
        self.tritium_inventory = sum(pump.species_inventories["Tritium"] for pump in self.pumps)
        return self.tritium_inventory

    def get_inflow(self):
        """
        Gets the total inflow rate from all input ports.

        Returns:
        --------
        float
            The total inflow rate.
        """
        inflow = 0
        for port in self.input_ports.values():
            inflow += port.flow_rate
        return inflow

    def store_flows(self):
        """Stores the flow rates (currently a placeholder method)."""
        pass

    def reset_system(self):
        """Resets the cryopump system to its initial state."""
        self.pumps = []  # List of pumps
        self.regenerating_pumps = []  # List of regenerating pumps
        self.active_pumps = []
        self.stand_by_pumps = []
        self.outflow = []
        self.inflow = []
        self.tritium_inventory = 0

    def calculate_inventory_derivative(self):
        """
        Calculates the derivative of the inventory.

        Returns:
        --------
        float
            The derivative of the inventory.
        """
        dydt = self.inflow[-1] - self.outflow[-1]
        return dydt

    def get_outflow(self):
        """
        Gets the latest outflow rate.

        Returns:
        --------
        float
            The latest outflow rate.
        """
        if not self.outflow:
            return 0
        else:
            return self.outflow[-1]

    def plot_inventories(self, CS):
        """
        Plots the inventory evolution for each pump.

        Parameters:
        -----------
        CS : ChemicalSpecies
            The chemical species involved in the cryopump system.
        """
        for pump in self.pumps:
            fig, ax = plt.subplots()
            ax.axhline(self.max_capacity, color='r', linestyle='--', label='Max Capacity')
            ax.axhline(self.max_hydrogen_capacity, color='b', linestyle='--', label='Max Hydrogen Capacity')
            ax.plot(pump.time_evolution[0:100], pump.total_inventory_evolution[0:100], label="Total")
            ax.plot(pump.time_evolution[0:100], pump.hydrogen_throughput_inventory_evolution[0:100], label="Hydrogen total (D+T)")
            for specie in CS.species.values():
                if specie.name in pump.species_inventory_evolution:
                    ax.plot(pump.time_evolution[0:100], pump.species_throughput_inventory_evolution[specie.name][0:100], label=specie.name)
                else:
                    print(f"Warning: {specie.name} not found in pump.species_inventory_evolution")
            plt.xlabel('Time (s)')
            plt.ylabel('Inventory [Pa*m^3]')
            plt.title(f"Inventory Evolution for {pump.name}")
            ax.legend()
            plt.show()

    def plot_inventories_togheter(self, CS):
        """
        Plots the inventory evolution for all pumps together.

        Parameters:
        -----------
        CS : ChemicalSpecies
            The chemical species involved in the cryopump system.
        """
        fig, ax = plt.subplots()
        ax.axhline(self.max_capacity, color='r', linestyle='--', label='Max Capacity')
        ax.axhline(self.max_hydrogen_capacity, color='b', linestyle='--', label='Max Hydrogen Capacity')
        for pump in self.pumps:
            ax.plot(pump.time_evolution[0:100], pump.total_inventory_evolution[0:100], label=f"{pump.name} - Total")
            ax.plot(pump.time_evolution[0:100], pump.hydrogen_throughput_inventory_evolution[0:100], label=f"{pump.name} - Hydrogen total (D+T)")
        plt.xlabel('Time (s)')
        plt.ylabel('Inventory [Pa*m^3]')
        plt.title(f"Inventory Evolution for all pumps")
        ax.legend()
        plt.show()

    def print_parameters(self, CS):
        """
        Prints the parameters of the cryopump system.

        Parameters:
        -----------
        CS : ChemicalSpecies
            The chemical species involved in the cryopump system.
        """
        print(f"Number of pumps: {len(self.active_pumps)}")
        print(f"Pump max capacity: {self.max_capacity} Pa*m^3")
        print(f"Max throughput of each pump: {CS.total_throughput} Pa*m^3/s")
        print(f"Max hydrogen throughput of each pump: {CS.species['Tritium'].throughput + CS.species['Deuterium'].throughput} Pa*m^3/s")
        print(f"Max mass flow rate of each pump: {CS.total_mass_flow_rate} Kg/s")
        print(f"Max particles flow rate of each pump: {CS.total_throughput} s^-1")

    def pump_deactivation(self, pump):
        """
        Deactivates a pump and moves it to stand-by and regenerating lists.

        Parameters:
        -----------
        pump : Pump
            The pump to be deactivated.
        """
        pump.deactivation()
        self.stand_by_pumps.append(pump)
        self.regenerating_pumps.append(pump)
        self.active_pumps.remove(pump)

    def pump_activation(self, pump):
        """
        Activates a pump and removes it from the regenerating list.

        Parameters:
        -----------
        pump : Pump
            The pump to be activated.
        """
        pump.activation()
        self.regenerating_pumps.remove(pump)

    def print_new_pump(self, time, mass_tritium_outflow, CS, intake, dt):
        """
        Prints the details of a newly added pump.

        Parameters:
        -----------
        time : float
            The current time.
        mass_tritium_outflow : float
            The mass of tritium outflow.
        CS : ChemicalSpecies
            The chemical species involved in the cryopump system.
        intake : float
            The intake value for the new pump.
        dt : float
            The time step for the update.
        """
        print(f"New pump added. Total pumps: {len(self.pumps)} at time {self.seconds_to_ymdhms(time)}")
        print(f"Active pumps: {len(self.active_pumps)}.")
        print(f"Regenerating pumps: {len(self.regenerating_pumps)} including {len(self.stand_by_pumps)} in stand-by")
        print(f"Total tritium outflow from VP: {mass_tritium_outflow} Kg")
        print(f"Tritium intake of the new pump: {CS.species['Tritium'].mass_intake} Kg")
        print(f"Throughput required from the new pump: {intake / dt} Pa*m^3/s")
        print(f"Hydrogen throughput required from the new pump: {intake * CS.hydrogen_throughput_intake_coefficient / dt} Pa*m^3/s\n\n")

    def switch_on_stand_by_pumps(self):
        """Switches on the stand-by pumps."""
        for pump in self.regenerating_pumps:
            if pump.stand_by:
                pump.stand_by = False
                self.stand_by_pumps.remove(pump)

    def seconds_to_ymdhms(self, seconds):
        """
        Converts seconds to a formatted string of years, months, days, hours, minutes, and seconds.

        Parameters:
        -----------
        seconds : int
            The number of seconds to be converted.

        Returns:
        --------
        str
            The formatted time string.
        """
        SECONDS_IN_MINUTE = 60
        SECONDS_IN_HOUR = 3600
        SECONDS_IN_DAY = 86400
        SECONDS_IN_MONTH = 2592000  # Approximate (30 days in a month)
        SECONDS_IN_YEAR = 31536000  # Approximate (365 days in a year)
        years = seconds // SECONDS_IN_YEAR
        seconds %= SECONDS_IN_YEAR
        months = seconds // SECONDS_IN_MONTH
        seconds %= SECONDS_IN_MONTH
        days = seconds // SECONDS_IN_DAY
        seconds %= SECONDS_IN_DAY
        hours = seconds // SECONDS_IN_HOUR
        seconds %= SECONDS_IN_HOUR
        minutes = seconds // SECONDS_IN_MINUTE
        seconds %= SECONDS_IN_MINUTE
        return f"{years}:{months:02}:{days:02}:{hours:02}:{minutes:02}:{seconds:02}"