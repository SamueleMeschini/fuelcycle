import numpy as np

kb = 1.380648e-23
R = 8.314  # J/molK
NA = R/kb

class Element:
    """
    A class to represent a chemical element.

    Attributes:
    -----------
    name : str
        The name of the element.
    molecular_mass : float
        The molecular mass of the element.
    nominal_pumping_speed : float
        The nominal pumping speed of the element.
    partial_pressure : float
        The partial pressure of the element.
    capture_coefficient : float
        The capture coefficient of the element.
    decay_constant : float, optional
        The decay constant of the element (default is 0).
    non_radioactive_loss : float, optional
        The non-radioactive loss of the element (default is 0).
    """

    def __init__(self, name, molecular_mass, nominal_pumping_speed, partial_pressure, capture_coefficient, k, decay_constant=0, non_radioactive_loss=0):
        """
        Constructs all the necessary attributes for the element object.

        Parameters:
        -----------
        name : str
            The name of the element.
        molecular_mass : float
            The molecular mass of the element.
        nominal_pumping_speed : float
            The nominal pumping speed of the element.
        partial_pressure : float
            The partial pressure of the element.
        capture_coefficient : float
            The capture coefficient of the element.
        decay_constant : float, optional
            The decay constant of the element (default is 0).
        non_radioactive_loss : float, optional
            The non-radioactive loss of the element (default is 0).
        """
        self.name = name
        self.molecular_mass = molecular_mass
        self.partial_pressure = partial_pressure
        self.decay_constant = decay_constant
        self.non_radioactive_loss = non_radioactive_loss 
        self.pumping_speed_coefficient = np.sqrt(2/molecular_mass) * capture_coefficient
        self.pumping_speed = nominal_pumping_speed * self.pumping_speed_coefficient
        self.dynamic_pumping_speed = self.pumping_speed
        self.k = k
        self.inventory = 0
        self.inventory_evolution = []
        self.partial_pressure_evolution = [partial_pressure]
        self.get_density(273.15)
        self.density_evolution = [self.density]
    

    def get_density(self, divertor_temperature):
        """
        Calculates the density of the element.

        Parameters:
        -----------
        divertor_temperature : float
            The temperature of the divertor.

        Returns:
        --------
        float
            The density of the element.
        """
        self.density = self.partial_pressure / kb / divertor_temperature
        return self.density

    def get_particles_flow_rate(self):
        """
        Calculates the particles flow rate of the element.

        Returns:
        --------
        float
            The particles flow rate of the element.
        """
        self.get_density(273.15)
        self.particles_flow_rate = self.density * self.dynamic_pumping_speed
    
    def get_mass_flow_rate(self):
        """
        Calculates the mass flow rate of the element.

        Returns:
        --------
        float
            The mass flow rate of the element in kg/s.
        """
        self.get_particles_flow_rate()
        self.mass_flow_rate = self.particles_flow_rate / NA * self.molecular_mass / 1e3  # kg/s

    
    def get_throughput(self):
        self.throughput = self.partial_pressure*self.dynamic_pumping_speed
    
    def get_dynamic_pumping_speed(self, saturation):
        #self.dynamic_pumping_speed = self.pumping_speed / (1 + np.exp(k * (saturation - 0.5)))
        self.dynamic_pumping_speed = self.pumping_speed * (1-(saturation**2/((saturation**2)+(1-saturation)**2))) * (1-saturation)**self.k
        #print(self.dynamic_pumping_speed)

class ChemicalSpecies:
    """
    A class to represent a collection of chemical species.

    Attributes:
    -----------
    species : dict
        A dictionary to store the chemical species.
    """
    
    def __init__(self):
        """Constructs all the necessary attributes for the chemical species object."""
        self.species = {}

    def add_species(self, specie):
        """
        Adds a species to the collection.

        Parameters:
        -----------
        specie : Element
            The chemical element to add.
        """
        self.species[specie.name] = specie
    
    def update_divertor_pressure(self, VP, TBE, N_burn):
        VP.total_pressure = 0
        SIGMA_HeT = VP.species_active_pumping_speed["Helium"]/VP.species_active_pumping_speed["Tritium"]
        f_HeT_div = TBE/(1-TBE)/SIGMA_HeT
        #I need to insert manually partial pressure becuase I need f_HeT_div from SIGMA_HeT which in turns needs me to first define the species 
        self.species["Tritium"].partial_pressure = VP.tritium_particles_flow_rate/(VP.species_active_pumping_speed["Tritium"])*kb*273.15
        self.species["Deuterium"].partial_pressure = VP.tritium_particles_flow_rate/(VP.species_active_pumping_speed["Deuterium"])*kb*273.15
        self.species["Helium"].partial_pressure = self.species["Tritium"].partial_pressure*f_HeT_div
        self.species["Neon"].partial_pressure = (self.species["Tritium"].partial_pressure+self.species["Deuterium"].partial_pressure+self.species["Helium"].partial_pressure)/100*3
        self.species["Argon"].partial_pressure = (self.species["Tritium"].partial_pressure+self.species["Deuterium"].partial_pressure+self.species["Helium"].partial_pressure)/100*2
        for specie in self.species.values():
            specie.get_density(273.15)
            specie.density_evolution.append(specie.density)
            specie.partial_pressure_evolution.append(specie.partial_pressure)
            VP.total_pressure+=specie.partial_pressure
        VP.total_pressure_evolution.append(VP.total_pressure)
        #print(self.species["Tritium"].partial_pressure)
        

    def get_total_particles_flow_rate(self):
        """Calculates the total particles flow rate of all species."""
        self.total_particles_flow_rate = 0
        for specie in self.species.values():
            specie.get_particles_flow_rate()          
            self.total_particles_flow_rate += specie.particles_flow_rate            

    def get_total_mass_flow_rate(self):
        """Calculates the total mass flow rate of all species."""
        self.total_mass_flow_rate = 0
        for specie in self.species.values():
            specie.get_mass_flow_rate()
            self.total_mass_flow_rate += specie.mass_flow_rate

    def get_total_throughput(self):
        """Calculates the total throughput of all species."""
        self.total_throughput = 0
        for specie in self.species.values():
            specie.get_mass_flow_rate()
            specie.throughput = (specie.mass_flow_rate * 1e3) / specie.molecular_mass * R * 273.15  # Pa*m^3*s^-1
            self.total_throughput += specie.throughput

    
    def get_species_mass_inflow(self, valve):
        """
        Calculates the mass inflow for each species based on the tritium mass inflow.

        Parameters:
        -----------
        tritium_mass_inflow : float
            The mass inflow of tritium.
        """
        self.total_mass_inflow=0
        for specie in self.species.values():
            specie.get_mass_flow_rate()
            specie.mass_inflow = specie.mass_flow_rate * valve
            self.total_mass_inflow += specie.mass_inflow

    def get_throughput_inflow(self, valve):
        """
        Calculates the throughput inflow for each species based on the tritium mass inflow.

        Parameters:
        -----------
        tritium_mass_inflow : float
            The mass inflow of tritium.
        """
        self.total_throughput_inflow = 0
        for specie in self.species.values():
            specie.get_throughput()
            specie.throughput_inflow = specie.throughput * valve
            self.total_throughput_inflow += specie.throughput_inflow
    
    def get_regeneration_throughput_outflow(self, pump, dt):
        for specie in self.species.values():
            specie.regeneration_throughput_outflow = pump.species_throughput_inventories[specie.name]/pump.regeneration_time*dt*pump.regeneration_valve

    def get_dynamic_pumping_speeds(self, saturation):
        self.total_dynamic_pumping_speed = 0
        for specie in self.species.values():
            specie.get_dynamic_pumping_speed(saturation)
            self.total_dynamic_pumping_speed+=specie.dynamic_pumping_speed
    
    def reset(self):
        self.species = {}