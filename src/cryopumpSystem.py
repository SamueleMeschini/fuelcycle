import numpy as np
from component import (Component)

class CryopumpSystem(Component):
    def __init__(self, name, max_capacity, throughput, regeneration_time, LAMBDA, non_radioactive_loss = 0, **kwargs):
        super().__init__(name, residence_time=1, **kwargs)
        self.LAMBDA = LAMBDA
        self.non_radioactive_loss = non_radioactive_loss
        self.name = name
        self.max_capacity = max_capacity  # Capacità massima della pompa
        self.throughput = throughput  # Velocità di pompaggio (flusso in ingresso massimo)
        self.regeneration_time = regeneration_time  # Tempo richiesto per rigenerare
        self.pumps = []  # Lista delle pompe 
        self.regenerating_pumps = []  # Liste delle pompe in rigenerazione
        self.outflow = []
        self.inflow = []
        self.tritium_inventory = 0

    def add_pump(self):
        """Aggiunge una nuova pompa attiva."""
        pump = {
            'inventory': 0,  # Inventario iniziale
            'active': True,
            'regenerating': False,
            'regen_time_left': 0
        }
        self.pumps.append(pump)
        #print(f"Nuova pompa aggiunta. Totale pompe: {len(self.pumps)}")

    def update_pumps(self, dt):
        """Aggiorna le pompe esistenti e verifica se ne servono di nuove."""
        total_inflow = self.get_inflow()*dt  # Flusso totale in ingresso
        total_outflow = 0  # Flusso totale in uscita
        total_inventory_change = 0
        
        # Verifica e aggiorna le pompe esistenti
        for pump in self.pumps:
            if pump['active']:
                intake = min(self.throughput * dt, total_inflow, self.max_capacity - pump['inventory'])
                pump['inventory'] += intake
                total_inflow -= intake
                total_inventory_change += intake
                
                # Se la pompa è piena, avvia la rigenerazione
                if pump['inventory'] >= self.max_capacity:
                    #print("pompa in rigenerazione")
                    pump['active'] = False
                    pump['regenerating'] = True
                    pump['regen_time_left'] = self.regeneration_time
                    self.regenerating_pumps.append(pump)
        pumps_to_remove = []
        # Aggiornamento delle pompe in rigenerazione
        for pump in self.regenerating_pumps:
            if pump['regenerating']:
                outake = min(self.max_capacity/self.residence_time*dt, pump['inventory'])
                pump['inventory'] -= outake
                total_outflow += outake
                total_inventory_change -= outake
                if pump['regen_time_left'] - dt <= 0:
                    #print(f"pompa attiva. Inventory residua: {pump['inventory']} Kg")
                    pump['regenerating'] = False
                    pump['active'] = True
                    #total_outflow += pump['inventory']  # Il trizio rigenerato va nel circuito
                    #total_inventory_change -= pump['inventory']
                    #pump['inventory'] = 0
                    #total_outflow = 0
                    pumps_to_remove.append(pump)
                else:
                    pump['regen_time_left'] -= dt
        for pump in pumps_to_remove:
            self.regenerating_pumps.remove(pump)
        # Controlla se servono nuove pompe
        if total_inflow > 0:
            #print(total_inflow)
            self.add_pump()
            self.pumps[-1]['inventory'] += min(self.throughput * dt, total_inflow)
            total_inventory_change += min(self.throughput * dt, total_inflow)
            total_inflow -= min(self.throughput * dt, total_inflow)
            print(f"Nuova pompa aggiunta. Totale pompe: {len(self.pumps)} at time {dt}")
            #print(total_inflow)
            #print("")
        # Bilancio di massa
        derivative = total_inventory_change/dt
        #print(f"Inflow: {self.get_inflow()*dt}, Outflow: {total_outflow}, Derivative: {derivative}")
        self.outflow.append(total_outflow/dt)
        self.inflow.append(self.get_inflow())
        return total_outflow, derivative

    def update_inventory(self, a, dt):
        self.update_pumps(dt)
        """Restituisce l'inventario totale di tutte le pompe."""
        self.tritium_inventory = sum(pump['inventory'] for pump in self.pumps)
        self.tritium_inventory = self.tritium_inventory * (1 - self.LAMBDA)
        return self.tritium_inventory
    def get_inflow(self):
        inflow = 0
        for port in self.input_ports.values():
            inflow += port.flow_rate
        return inflow
    def store_flows(self):
        #self.inflow.append(self.get_inflow())
        pass
    def reset_system(self):
        self.pumps = []  # Lista delle pompe 
        self.regenerating_pumps = []  # Liste delle pompe in rigenerazione
        self.outflow = []
        self.inflow = []
    def calculate_inventory_derivative(self):
        dydt = self.inflow[-1]-self.outflow[-1]*(1+self.non_radioactive_loss)-self.tritium_inventory*self.LAMBDA
        return dydt
    def get_outflow(self):
        if self.outflow == []:
            return 0
        else:
            return self.outflow[-1]