from component import Component
from pulsedSource import PulsedSource

class BreedingBlanket(Component, PulsedSource):
    def __init__(self, name, residence_time,  N_burn, TBR, AF, pulse_period, initial_inventory=0, non_radioactive_loss=0.0001, *args, **kwargs):
        # super().__init__(name, residence_time, initial_inventory, non_radioactive_loss, **kwargs)
        Component.__init__(self, name, residence_time, initial_inventory, non_radioactive_loss, *args, **kwargs)
        PulsedSource.__init__(self, amplitude=N_burn, pulse_duration=pulse_period*AF, pulse_period=pulse_period)      

        self.N_burn = N_burn
        self._TBR = TBR  # Initialize _TBR directly
        self.tritium_source = self.N_burn * self.TBR * self.get_pulse()  # Initialize tritium_source directly

    @property
    def TBR(self):
        return self._TBR

    @TBR.setter
    def TBR(self, value):
        self._TBR = value
        self.tritium_source = self.N_burn * self.TBR * self.get_pulse()


