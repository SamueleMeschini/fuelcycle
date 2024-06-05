class PulsedSource:
    def __init__(self, amplitude, pulse_duration, pulse_period):
        """
        Initializes a PulsedSource object.

        Parameters:
        amplitude (float): The amplitude of the pulse.
        pulse_duration (float): The duration of each pulse.
        pulse_period (float): The period between pulses.
        """
        self.amplitude = amplitude
        self.pulse_duration = pulse_duration
        self.pulse_period = pulse_period
        self.current_time = 0

    def set_current_time(self, time):
        """
        Sets the current time to zero.
        """
        self.current_time = time

    def get_current_time(self):
        """
        Returns the current time.
        """
        return self.current_time

    def get_pulse(self):
        """
        Returns the value of the pulse at the given time.

        Parameters:
        current_time (float): The current time.

        Returns:
        float: The value of the pulse at the given time.
        """
        pulse_time = self.get_current_time() % self.pulse_period
        if pulse_time < self.pulse_duration:
            return self.amplitude # Pulse on
        else:
            return 0. # Pulse off
