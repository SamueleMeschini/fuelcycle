from .component import Component

class Plasma(Component):
    def __init__(self, name, N_burn, TBE, fp_fw, fp_div, **kwargs):
        """
        Initialize a Plasma object.

        Args:
            name (str): The name of the plasma.
            N_burn (float): The burn rate of the plasma.
            TBE (float): The tritium burnup efficiency of the plasma.
            **kwargs: Additional keyword arguments.
Z
        """
        super().__init__(name, residence_time=1, **kwargs)
        self.N_burn = N_burn
        self.TBE = TBE
        self.fp_fw = fp_fw
        self.fp_div = fp_div

    def get_outflow(self):
        """
        Calculate the outflow rate of the plasma.

        Returns:
            float: The outflow rate of the plasma.

        """
        return (1 - self.TBE - self.fp_div - self.fp_fw) / self.TBE * self.N_burn 
    
    def calculate_inventory_derivative(self):
        """
        Calculate the derivative of the plasma inventory.

        Returns:
            float: The derivative of the plasma inventory.

        """
        inflow = self.get_inflow()
        outflow = self.get_outflow()
        dydt = inflow - outflow  - self.N_burn
        return dydt
