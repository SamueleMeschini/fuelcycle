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

    def __init__(self, name, molecular_mass, nominal_pumping_speed, partial_pressure, capture_coefficient, decay_constant=0, non_radioactive_loss=0):
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
        self.inventory = 0
        self.inventory_evolution = []

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
        self.particles_flow_rate = self.density * self.pumping_speed
        return self.particles_flow_rate
    
    def get_mass_flow_rate(self):
        """
        Calculates the mass flow rate of the element.

        Returns:
        --------
        float
            The mass flow rate of the element in kg/s.
        """
        self.mass_flow_rate = self.particles_flow_rate / NA * self.molecular_mass / 1e3  # kg/s
        return self.mass_flow_rate


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

    def get_intake_coefficients(self):
        """Calculates the intake coefficients for all species."""
        self.get_total_particles_flow_rate()
        self.get_total_mass_flow_rate()
        self.get_total_throughput()
        for specie in self.species.values(): 
            specie.particles_intake_coefficient = specie.particles_flow_rate / self.total_particles_flow_rate
            specie.mass_intake_coefficient = specie.mass_flow_rate / self.total_mass_flow_rate
            specie.throughput_intake_coefficient = specie.throughput / self.total_throughput
        self.hydrogen_throughput_intake_coefficient = self.species["Tritium"].throughput_intake_coefficient + self.species["Deuterium"].throughput_intake_coefficient

    def get_species_mass_inflow(self, tritium_mass_inflow):
        """
        Calculates the mass inflow for each species based on the tritium mass inflow.

        Parameters:
        -----------
        tritium_mass_inflow : float
            The mass inflow of tritium.
        """
        self.total_mass_inflow = tritium_mass_inflow / self.species["Tritium"].mass_intake_coefficient
        for specie in self.species.values():
            specie.mass_inflow = self.total_mass_inflow * specie.mass_intake_coefficient

    def get_throughput_inflow(self, tritium_mass_inflow):
        """
        Calculates the throughput inflow for each species based on the tritium mass inflow.

        Parameters:
        -----------
        tritium_mass_inflow : float
            The mass inflow of tritium.
        """
        self.get_species_mass_inflow(tritium_mass_inflow)
        self.total_throughput_inflow = 0
        for specie in self.species.values():
            specie.throughput_inflow = (specie.mass_inflow * 1e3) / specie.molecular_mass * R * 273.15  # Pa*m^3
            self.total_throughput_inflow += specie.throughput_inflow

    def get_species_mass_intake(self, intake):
        """
        Calculates the mass intake for each species based on the intake value.

        Parameters:
        -----------
        intake : float
            The intake value.
        """
        for specie in self.species.values():
            specie.throughput_intake = (intake * specie.throughput_intake_coefficient)
            specie.mass_intake = specie.throughput_intake / 273.15 / R * specie.molecular_mass / 1e3  # kg