import numpy as np
from .component import Component
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

    def __init__(self, name, max_capacity, max_hydrogen_capacity, pumping_speed, regeneration_time, CS, LAMBDA, TBE, N_burn, non_radioactive_loss=1e-4, **kwargs):
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
        self.regenerating_limit = 0.10 #could be a function of the pump and decrease with number of pumps. so first pumps operates often, last pumps regenerate deeper
        
        self.species_active_pumping_speed = {specie.name: specie.dynamic_pumping_speed for specie in CS.species.values()} 
        self.species_particle_flow_rate = {specie.name: 0 for specie in CS.species.values()} 
        self.species_throughput = {specie.name: 0 for specie in CS.species.values()} 
        self.species_mass_flow_rate = {specie.name: 0 for specie in CS.species.values()} 
        self.pumps = [] 
        self.regenerating_pumps = []  
        self.active_pumps = []
        self.stand_by_pumps = []
        self.outflow = [0]
        self.inflow = [0]
        self.tritium_inventory = 0
        self.divertor_pressure_time_plot = [0]
        self.divertor_density_time_plot = [0]
        self.total_pressure_evolution = [0]
        

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

    def update_pumps(self, dt, time, CS, TBE, N_burn):
    
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
        total_tritium_inflow = self.get_inflow() * dt  # tritium kg
        mass_tritium_inflow = 0
        mass_tritium_outflow = 0  # Total outflow

        self.tritium_particles_flow_rate = self.get_inflow()  * NA / (CS.species["Tritium"].molecular_mass/1e3)
        CS.update_divertor_pressure(self, TBE, N_burn)      
        self.divertor_pressure_time_plot.append(time)
        self.divertor_density_time_plot.append(time)
        self.species_active_pumping_speed = {specie.name: 0 for specie in CS.species.values()}

        #print(specie.partial_pressure for specie in CS.species.values())

        for pump in self.pumps:
            if pump.active:
                #if time%(100*dt) ==0:
                    #print(f"{pump.name} is working, {time}")
                if pump not in self.active_pumps:
                    self.active_pumps.append(pump)
                    
                    #print(f"{pump.name} activated, {time}")
                    #print(f"{pump.name} is active again")
                    #print(f"{pump.total_throughput_inventory} Pa*m^3,{pump.saturation} saturation")
                    #print(f"{pump.total_throughput_inflow}")
                    #print(f"{(pump.species_throughput_inflow["Tritium"] + pump.species_throughput_inflow["Deuterium"])}")
                #print(f"{pump.name}, {pump.total_mass_inventory} a")
                #CS.get_dynamic_pumping_speeds(pump.saturation)
                pump.update_pumping_speed(CS)
                #print(f"{pump.name}, {CS.total_dynamic_pumping_speed}")
                #CS.species["Tritium"].get_mass_flow_rate()
                pump.get_pump_mass_flow_rate(CS)
                pump.update_valve(total_tritium_inflow/dt, CS)
                #print(pump.name, pump.valve)
                pump.get_pump_throughput_inflow(CS)
                #mass_tritium_inflow += 
                #if time%(100*dt) ==0:
                #print(f"{pump.name} is active, {pump.total_throughput_inventory}, {pump.total_throughput_inflow}, {pump.valve}, {time}")
                #pump.get_pump_throughput_inflow(CS)  # Pa*m^3
                if pump.valve < 1e-12:
                    if pump.total_throughput_inventory > pump.max_capacity*self.regenerating_limit: 
                        pump.active = False
                        pump.regenerating = True
                        self.regenerating_pumps.append(pump)
                        self.active_pumps.remove(pump)
                        #print(f"{pump.name} deactivated because inactive, {time}, {pump.total_throughput_inventory} \n")
                        continue
                    else:
                        pump.valve = 0
                        pump.get_pump_throughput_inflow(CS)
                        pump.get_pump_mass_flow_rate_inflow(CS)
                        pump.update_active_pump(CS, time, dt)
                        #print(f"{pump.name} is waiting")
                        #print(pump.valve, pump.total_throughput_inventory, time, "\n")
                        continue
                pump.get_limiting_factor(self, dt)
                for specie in CS.species.values():
                    self.species_active_pumping_speed[specie.name]+=pump.species_pumping_speed[specie.name]*pump.valve
                pump.get_pump_throughput_inflow(CS)
                pump.get_pump_mass_flow_rate_inflow(CS)
                #CS.get_species_mass_inflow(pump.valve)
                #print(f"{pump.name} tritium mass inflow {CS.species["Tritium"].mass_inflow}")
                
                #print(f"{pump.name} is active, {pump.total_throughput_inventory}, {pump.total_throughput_inflow}, {pump.valve}, {time}, {total_tritium_inflow}")
                #print(f"{pump.name} is active, saturation = {pump.saturation}, valve = {pump.valve}, time = {time}")
                pump.update_active_pump(CS, time, dt)
                total_tritium_inflow -= pump.species_mass_flow_rate_inflow["Tritium"]*dt
                #print(f"{pump.name}, {CS.species["Tritium"].mass_inflow*dt}, {pump.species_mass_inventory_evolution["Tritium"][-1]-pump.species_mass_inventory_evolution["Tritium"][-2]}, {time}")
                #if time>1838000:
                    #print(total_tritium_inflow)
                #if time>62000:
                    #print(pump.name, pump.hydrogen_throughput_inventory, pump.valve, pump.limiting_factor, time)
                #if pump.total_throughput_inventory >= pump.max_capacity or pump.hydrogen_throughput_inventory >= pump.max_hydrogen_capacity:
                    #pump.temporary_total_inventory = pump.total_inventory
                    #self.pump_deactivation(pump)


        for pump in self.pumps:
            if pump.regenerating == True:
                if pump.stand_by == True:
                    pass
                else:
                    tritium_mass_inventory_before= pump.species_mass_inventory["Tritium"]
                    #if time%(10*dt) == 0:
                    #print(f"tritium mass of {pump.name}, {pump.species_mass_inventory["Tritium"]}")
                        #print(f"deuterium mass of {pump.name}, {pump.species_mass_inventory["Deuterium"]}")
                        #print(f"tritium throughput of {pump.name}, {pump.species_throughput_inventory["Tritium"]}")
                        #print(f"total throughput of {pump.name}, {pump.total_throughput_inventory}\n\n")
                    pump.update_regenerating_pump(CS, time, dt)
                    tritium_mass_inventory_after= pump.species_mass_inventory["Tritium"]
                    #print(f"{pump.name}, {pump.species_mass_inventory["Tritium"]}\n\n\n")
                    #print(f"{pump.name} is regenerating", pump.total_throughput_inventory)
                    #print(f"{pump.name}, {pump.total_mass_inventory} r")
                    #print(f"{pump.name}, {pump.total_throughput_inventory} r")
                    #tritium_mass_inventory = pump.species_mass_inventory_evolution["Tritium"]
                    #self.mass_tritium_outflow += pump.species_mass_inventory_evolution["Tritium"][-2]-pump.species_mass_inventory_evolution["Tritium"][-1]
                    mass_tritium_outflow += tritium_mass_inventory_before-tritium_mass_inventory_after
                    #print(mass_tritium_outflow, time)
                    #mass_tritium_outflow += tritium_mass_inventory[-2]-tritium_mass_inventory[-1]
                    #mass_tritium_outflow += pump.species_throughput_inventory_evolution["Tritium"][-2]-pump.species_throughput_inventory_evolution["Tritium"][-1]
                    #mass_tritium_outflow -= CS.species["Tritium"].mass_intake #positive number, kg
                    #pump.regen_time_left -= dt
                    if pump.total_throughput_inventory <= pump.max_capacity*self.regenerating_limit:
                        self.pump_activation(pump)
                        #print(f"AAAAAAAA {pump.name} has been activated, {pump.total_throughput_inventory}")

        while total_tritium_inflow > 1e-8:
            self.add_pump(CS)
            #CS.get_dynamic_pumping_speeds(self.pumps[-1].saturation)
            #self.pumps[-1].update_pumping_speed(CS)
            #CS.species["Tritium"].get_mass_flow_rate()
            self.pumps[-1].get_pump_mass_flow_rate(CS)
            self.pumps[-1].update_valve(total_tritium_inflow/dt, CS)
            self.pumps[-1].get_pump_throughput_inflow(CS)  # Pa*m^3
            self.pumps[-1].get_limiting_factor(self, dt)
            for specie in CS.species.values():
                self.species_active_pumping_speed[specie.name]+=self.pumps[-1].species_pumping_speed[specie.name]*self.pumps[-1].valve
            self.pumps[-1].get_pump_throughput_inflow(CS)
            self.pumps[-1].get_pump_mass_flow_rate_inflow(CS)
            self.pumps[-1].update_active_pump(CS, time, dt)
            total_tritium_inflow -= self.pumps[-1].species_mass_flow_rate_inflow["Tritium"]*dt
            print(self.get_inflow(), CS.species["Tritium"].partial_pressure, total_tritium_inflow)
            self.print_new_pump(time, mass_tritium_outflow, CS, dt, self.pumps[-1])

        
                    
        #print(time, self.species_active_pumping_speed.values(), "\n\n")

        self.switch_on_stand_by_pumps()
        #self.outflow.append(mass_tritium_outflow / dt * (1 - CS.species["Tritium"].decay_constant))
        self.outflow.append(mass_tritium_outflow/dt)
        inflow = self.get_inflow()
        #for pump in self.pumps:
            #inflow += pump.species_mass_inventory_evolution["Tritium"][-1]-pump.species_mass_inventory_evolution["Tritium"][-2]
        self.inflow.append(inflow)
        #print(self.outflow[-1], self.inflow[-1], mass_tritium_outflow, time)
       
        self.total_inventory = 0
        for pump in self.pumps:
            self.total_inventory += pump.total_throughput_inventory
            #print(total_inventory, self.tritium_inventory, time, mass_tritium_outflow, inflow, self.get_inflow()*dt)
        total_throughput_inflow = 0
        #for pump in self.pumps:
            #total_throughput_inflow += pump.species_throughput_inventory_evolution["Tritium"][-1]-pump.species_throughput_inventory_evolution["Tritium"][-2]
        #self.inflow_throughput.append(inflow/dt)

    def update_inventory(self, dt, time, CS, TBE, N_burn):
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
        self.update_pumps(dt, time, CS, TBE, N_burn)
        #print("\n")
        self.tritium_inventory = sum(pump.species_mass_inventory["Tritium"] for pump in self.pumps)
        #self.species_active_pumping_speed = {specie.name: 0 for specie in CS.species.values()} 


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

    def get_particle_flow_rate(self, CS):
        self.species_particles_flow_rate["Tritium"] = self.get_inflow() * NA / (CS.species["Tritium"].molecular_mass/1e3)


    def store_flows(self):
        """Stores the flow rates (currently a placeholder method)."""
        pass

    def reset_system(self, CS):
        """Resets the cryopump system to its initial state."""
        self.pumps = [] 
        self.regenerating_pumps = []  
        self.active_pumps = []
        self.stand_by_pumps = []
        self.outflow = [0]
        self.inflow = [0]
        self.tritium_inventory = 0
        #CS.reset()

    def calculate_inventory_derivative(self):
        """
        Calculates the derivative of the inventory.

        Returns:
        --------
        float
            The derivative of the inventory.
        """
        #print(self.inflow, self.outflow)
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
            ax.plot(pump.time_evolution[0:100], pump.total_throughput_inventory_evolution[0:100], label="Total")
            ax.plot(pump.time_evolution[0:100], pump.hydrogen_throughput_inventory_evolution[0:100], label="Hydrogen total (D+T)")
            for specie in CS.species.values():
                if specie.name in pump.species_inventory_evolution:
                    ax.plot(pump.time_evolution[0:1000], pump.species_throughput_inventory_evolution[specie.name][0:1000], label=specie.name)
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
            ax.plot(pump.time_evolution[0:100], pump.total_throughput_inventory_evolution[0:100], label=f"{pump.name} - Total")
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

    def print_new_pump(self, time, mass_tritium_outflow, CS, dt, pump):
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
        #print(f"New pump added. Total pumps: {len(self.pumps)} at time {self.seconds_to_ymdhms(time)}")
        print(f"New pump added. Total pumps: {len(self.pumps)} at time {time}")
        print(f"Active pumps: {len(self.active_pumps)}.")
        print(f"Regenerating pumps: {len(self.regenerating_pumps)} including {len(self.stand_by_pumps)} in stand-by")
        print(f"Total tritium outflow from VP: {mass_tritium_outflow} Kg")
        print(f"Tritium intake of the new pump: {pump.species_mass_flow_rate_inflow['Tritium']*dt} Kg")
        print(f"Throughput required from the new pump: {(pump.total_throughput_inventory_evolution[-1]-pump.total_throughput_inventory_evolution[-2]) / dt} Pa*m^3/s")
        print(f"Hydrogen throughput required from the new pump: {(pump.hydrogen_throughput_inventory_evolution[-1]-pump.hydrogen_throughput_inventory_evolution[-2]) / dt} Pa*m^3/s\n\n")

    def switch_on_stand_by_pumps(self):
        """Switches on the stand-by pumps."""
        for pump in self.regenerating_pumps:
            if pump.stand_by:
                pump.stand_by = False
                self.stand_by_pumps.remove(pump)
                #print(f"{pump.name} reactivated from stand_by mode, {pump.regenerating}, {pump.active}")
                if pump.total_throughput_inventory <= 0:
                        self.pump_activation(pump)
                        print(f"{pump.name} reactivated from stand_by mode, {pump.regenerating}, {pump.active}")
    
    def plot_dynamic_pumping_speed(self, CS):
        saturation = np.linspace(0,1,100)
        for specie in CS.species.values():
            specie.get_dynamic_pumping_speed(saturation)
        fig, ax = plt.subplots()
        ax.axvline(self.regenerating_limit, linestyle='--', label='Regeneration lower limit')
        ax.axvline(self.max_hydrogen_capacity/self.max_capacity, color='r', linestyle='--', label='Max Hydrogen Capacity')
        #ax.axhline(self.max_hydrogen_capacity, color='b', linestyle='--', label='Max Hydrogen Capacity')
        for specie in CS.species.values():
            ax.plot(saturation ,specie.dynamic_pumping_speed, label=f"{specie.name}")
        plt.xlabel('Surface Saturation (-)')
        plt.ylabel('Pumping speed (m^3/s) ')
        plt.title(f"Dynamic pumping speed")
        ax.legend()
        plt.show()

    def plot_desorption_throughput(self):
        saturation = np.linspace(0,1,100)
        fig, ax = plt.subplots()
        ax.axvline(self.regenerating_limit, linestyle='--', label='Regeneration lower limit')
        ax.axvline(self.max_hydrogen_capacity/self.max_capacity, color='r', linestyle='--', label='Max Hydrogen Capacity')
        #ax.axhline(self.max_hydrogen_capacity, color='b', linestyle='--', label='Max Hydrogen Capacity')
        ax.plot(saturation ,self.max_capacity/self.regeneration_time*saturation**2/((saturation**2)+(1-saturation)**2), label=f"Desorption throughput", color='black')
        plt.xlabel('Surface Saturation (-)')
        plt.ylabel('Desorption throughput (Pa*m^3/s) ')
        plt.title(f"Desorption throughput")
        ax.legend()
        plt.show()

    def plot_partial_pressure_evolution(self,CS,TBE):
        fig, ax = plt.subplots()
        #ax.axhline(self.max_capacity, color='r', linestyle='--', label='Max Capacity')
        #ax.axhline(self.max_hydrogen_capacity, color='b', linestyle='--', label='Max Hydrogen Capacity')
        for specie in CS.species.values():
            ax.plot(self.divertor_pressure_time_plot[1:100], specie.partial_pressure_evolution[1:100], label=f"{specie.name}")
        ax.plot(self.divertor_pressure_time_plot[1:100], self.total_pressure_evolution[1:100], label=f"Total")
        plt.xlabel('Time (s)')
        plt.ylabel('Pressure (Pa)')
        plt.title(f"Divertor partial pressure evolution, TBE = {TBE}")
        ax.legend()
        plt.show()

    def plot_density_evolution(self,CS, TBE):
        fig, ax = plt.subplots()
        #ax.axhline(self.max_capacity, color='r', linestyle='--', label='Max Capacity')
        #ax.axhline(self.max_hydrogen_capacity, color='b', linestyle='--', label='Max Hydrogen Capacity')
        for specie in CS.species.values():
            ax.plot(self.divertor_density_time_plot[1:100], specie.density_evolution[1:100], label=f"{specie.name}")
        ax.set_yscale('log')
        plt.xlabel('Time (s)')
        plt.ylabel('Density (m^-3)')
        plt.title(f"Divertor density evolution, TBE = {TBE}")
        ax.legend()
        plt.show()

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