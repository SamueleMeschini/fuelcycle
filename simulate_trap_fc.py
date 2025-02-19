import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
seconds_to_years = 1/(60*60*24*365)

class Simulate:
    def __init__(self, dt, final_time, I_reserve, component_map, dt_max=100, max_simulations = 100, TBRr_accuraty = 1e-3, target_doubling_time = 2):
        """
        Initialize the Simulate class.

        Args:
        - dt: Time step size.
        - final_time: Final simulation time.
        - component_map: Mapping of component names to Component objects.
        """
        self.trap = 0
        self.dpa_vector = []
        self.traps_vector = []
        self.dpa = 0
        self.dt = dt
        self.initial_step_size = dt
        self.dt_max = dt_max
        self.final_time = final_time
        self.time = []
        self.initial_conditions = {name: component.tritium_inventory for name, component in component_map.components.items()}
        self.I_startup = component_map.components['Fueling System'].tritium_inventory
        self.y = [list(self.initial_conditions.values())]  # Initialize y with the initial conditions
        self.components = component_map.components
        self.component_map = component_map
        self.interval = self.final_time / 100
        self.TBRr_accuracy = TBRr_accuraty
        self.target_doubling_time = target_doubling_time # years 
        self.doubling_time = None
        self.I_reserve = I_reserve
        self.simulation_count = 0
        self.max_simulations = max_simulations

    def run(self, tolerance = 1e-3):
        """
        Run the simulation.

        Returns:
        - t: Array of time values.
        - y: Array of component inventory values.
        """
        while True:
            self.simulation_count += 1
            self.y[0] = [component.tritium_inventory for component in self.components.values()] # self.initial_conditions, possibly updated by the restart method
            t,y ,dpa_vector, trap_vector = self.forward_euler()
            self.doubling_time = self.compute_doubling_time(t,y)
            print(self.components['BB'].residence_time)
            print(trap_vector[-1])
            print(f"Doubling timee: {self.doubling_time}")
            print('Startup inventory is: {} \n'.format(y[0][0]))
            t_years = np.array(t)*seconds_to_years
            if self.simulation_count == 1:
                plt.figure()
                plt.plot(t_years, dpa_vector, label='Radiation damage in the BB')
                plt.plot(t_years, trap_vector, label='Trap denisty normalized')
                plt.xlabel('Time [y]')
                plt.ylabel('Damage [dpa]')
                plt.legend()
                plt.grid(True, which='both', linestyle='--', linewidth=0.5)
                plt.title("Case 3")
                plt.show()


            if (np.array(self.y)[:,0] - self.I_reserve < -tolerance).any() and self.simulation_count < self.max_simulations: # Increaase startup inventory if at any point the tritium inventory in the Fueling System component is below zero
                # self.y.pop() # remove the last element of y whose time is greater than the final time
                # return t,y
                difference = np.min(np.array(self.y)[:,0] - self.I_reserve)
                print("Error: Tritium inventory in Fueling System is below zero. Difference is {} kg".format(difference))
                self.update_I_startup(difference)
                print(f"Updated I_startup to {self.I_startup}")
                self.restart()
            elif self.doubling_time >= self.target_doubling_time or np.isnan(self.doubling_time) and self.simulation_count < self.max_simulations:
                # self.y.pop() # remove the last element of y whose time is greater than the final time
                # return t,y
                self.restart()
                self.components['BB'].TBR += self.TBRr_accuracy
                print('Updated TBR at {}. Production is now {}'.format(self.components['BB'].TBR, self.components['BB'].tritium_source))
            else:
                self.y.pop() # remove the last element of y whose time is greater than the final time
                return t,y
            
    def compute_doubling_time(self, t, y):
        """
        Compute the doubling time of the tritium inventory in the Fueling System component.

        Args:
        - t: Array of time values.
        - y: Array of component inventory values.

        Returns:
        - doubling_time: The doubling time of the tritium inventory.
        """
        I = np.array(self.y)[:,0] # Tritium inventory in the Fueling System component
        I_0 = self.I_startup
        print(f'I_0 = {I_0} kg')
        doubling_time_index = np.where((I - 2 * I_0) >= 0)[0]
        if len(doubling_time_index) == 0:
            return np.nan
        else:
            doubling_time = t[doubling_time_index[0]] * seconds_to_years
            return doubling_time
    
    def update_I_startup(self, margin):
        """
        Update the initial tritium inventory of the Fueling System component.
        """
        self.I_startup -= margin
        self.initial_conditions['Fueling System'] = self.I_startup

    def update_timestep(self, dt):
        """
        Update the time step size.

        Args:
        - dt: New time step size.
        """
        self.dt = dt
        self.n_steps = int(self.final_time / dt)


    def adaptive_timestep(self,y_new, y, t, tol=1e-6, min_dt=1e-6):
        """
        Perform adaptive time stepping.
        """
        p = 1 # Order of the method
        error = np.linalg.norm(y_new - (y + self.dt * self.f(y_new)))
        # Adjust time step size
        dt_new = self.dt * (tol / error)**p
        if abs(t % self.interval) < 10:
            print(f"Time = {t}, Error = {error}, dt = {self.dt}, dt_new = {dt_new}", end='\r')
        # Compute the new time step size based on the definition of adaptive timestep
        if t < 1000:
            dt_new = min(10, max(min_dt, dt_new))
        else:
            dt_new = min(self.dt_max, max(min_dt, dt_new))
        self.update_timestep(dt_new)

    def restart(self):
        """
        Restart the simulation by resetting time and component inventory.
        """
        self.time = []
        self.y = []
        self.dpa_vector = []
        self.traps_vector = []
        self.dpa = 0
        self.trap = 0
        self.components['BB'].residence_time = 3600 
        self.dt = self.initial_step_size
        for component, initial_condition in zip(self.components.values(), self.initial_conditions.values()):
            component.tritium_inventory = initial_condition
        self.y = [list(self.initial_conditions.values())]

    def forward_euler(self):
        """
        Perform the forward Euler integration method.

        Returns:
        - time: Array of time values.
        - y: Array of component inventory values.
        """
        t = 0
        print(f'Initial inventories = {self.y[0]} kg')
        while t < self.final_time:
            self.components['BB'].residence_time += (self.trap*10) * t *seconds_to_years
            self.dpa = (self.damage_rate(t))
            self.dpa_vector.append(self.dpa)
            self.trap = self.traps_linear(self.dpa)          
            self.traps_vector.append(self.trap)
            # Store flows
            for component in self.components.values():
                component.store_flows()
            if abs(t % self.interval) < 10:
                print(f"Percentage completed = {abs(t - self.final_time)/self.final_time * 100:.1f}%", end='\r')
            dydt = self.f(self.y[-1])
            y_new = self.y[-1] + self.dt * dydt
            self.time.append(t)
            for i, component in enumerate(self.components.values()):
                component.update_inventory(y_new[i])
            self.component_map.update_flow_rates()
            self.adaptive_timestep(y_new, self.y[-1], t)  # Update the timestep based on the new and old y values
            t += self.dt
            self.y.append(y_new) # append y_new after updating the time step        
        return [self.time, self.y, self.dpa_vector, self.traps_vector]


    def f(self, y):
        """
        Calculate the derivative of component inventory.

        Args:
        - y: Array of component inventory values.

        Returns:
        - dydt: Array of derivative values.
        """
        dydt = np.zeros_like(y)
        for i, component in enumerate(self.components.values()):
            dydt[i] += component.calculate_inventory_derivative()
        return dydt
    def damage_rate(self, t):
        damage_constant = 10 * seconds_to_years #dpa/s --> 10dpa/year
        dpa = damage_constant * np.array(t)
        return dpa
    def traps_linear(self, dpa):
        if dpa == 0:
            traps = dpa
        else:
            traps = dpa/20
        return traps
    def traps_logaritmic(self, dpa):
        if dpa == 0:
            traps = dpa
        else:
            traps = np.log(dpa+1)/20
        return traps
        