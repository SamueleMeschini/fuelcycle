import numpy as np
from component import (Component)
import time as tp

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
        self.active_pumps = []
        self.outflow = []
        self.inflow = []
        self.tritium_inventory = 0

    def add_pump(self):
        """Aggiunge una nuova pompa attiva."""
        pump = {
            'name': f"Pompa numero {(len(self.pumps))+1}",
            'inventory': 0,  # Inventario iniziale
            'active': True,
            'regenerating': False,
            'deactivation': False,
            'regen_time_left': 0, 
            'inventory_evolution': []
        }
        self.pumps.append(pump)
        self.active_pumps.append(pump)
        #print(f"Nuova pompa aggiunta. Totale pompe: {len(self.pumps)}")

    def update_pumps(self, a, dt, time):
        """Aggiorna le pompe esistenti e verifica se ne servono di nuove."""
        total_inflow = self.get_inflow()*dt  # Flusso totale in ingresso
        total_outflow = 0  # Flusso totale in uscita
        total_inventory_change = 0
        
        # Verifica e aggiorna le pompe esistenti
        pumps_to_remove_active = []
        for pump in self.pumps:
            if pump["active"] == True:
                if pump not in self.active_pumps:
                    self.active_pumps.append(pump)
                intake = min(self.throughput * dt, total_inflow, self.max_capacity - pump['inventory'])
                pump['inventory'] += intake
                total_inflow -= intake
                total_inventory_change += intake
                
                # Se la pompa è piena, avvia la rigenerazione
                if pump['inventory'] >= self.max_capacity:
                    #print("pompa in rigenerazione")
                    pump['deactivation'] = True
                    pump['active'] = False
                    pump['regenerating'] = True
                    pump['regen_time_left'] = self.regeneration_time
                    pumps_to_remove_active.append(pump)
                    self.regenerating_pumps.append(pump)
        for pump in pumps_to_remove_active:
            self.active_pumps.remove(pump)
        pumps_to_remove = []
        # Aggiornamento delle pompe in rigenerazione
        for pump in self.regenerating_pumps:
            if pump['deactivation'] == True:
                pass
            else:
                if pump['regenerating']:
                    outake = min(self.max_capacity/self.regeneration_time*dt, pump['inventory'])
                    pump['inventory'] -= outake
                    total_outflow += outake
                    total_inventory_change -= outake
                    if pump['regen_time_left'] - dt <= 0:
                        #print(f"pompa attiva. Inventory residua: {pump['inventory']} Kg")
                        outake = pump['inventory']
                        total_outflow += outake
                        total_inventory_change -= outake
                        pump['regenerating'] = False
                        pump['active'] = True
                        #self.active_pumps["pump"]
                        #total_outflow += pump['inventory']  # Il trizio rigenerato va nel circuito
                        #total_inventory_change -= pump['inventory']
                        #pump['inventory'] = 0
                        #total_outflow = 0
                        pumps_to_remove.append(pump)
                    else:
                        pump['regen_time_left'] -= dt
      
        # Controlla se servono nuove pompe
        if total_inflow > 0:
            #print(total_inflow)
            self.add_pump()
            self.pumps[-1]['inventory'] += min(self.throughput * dt, total_inflow)
            total_inventory_change += min(self.throughput * dt, total_inflow)
            total_inflow -= min(self.throughput * dt, total_inflow)
            print(f"Nuova pompa aggiunta. Totale pompe: {len(self.pumps)} at time {time/3600} [hours]")
            print(f"Pompe attive: {len(self.active_pumps)}.") 
            print(f"Pompe in rigenerazione: {len(self.regenerating_pumps)} di cui pompe in deattivazione: {self.regenerating_pumps.count("deactivation"==True)}")
            print(f"Outflow: {total_outflow} Kg\n")
            #print(total_inflow)
            #print("")
        for pump in pumps_to_remove: #controlla tutto l'oggetto e non solo il nome, non è efficiente
            #for p in self.regenerating_pumps: #Modifica di Andre: funziona
                #if p["name"] == pump["name"]:
            self.regenerating_pumps.remove(pump)
        for pump in self.regenerating_pumps:
            if pump['deactivation'] == True:
                pump['deactivation'] = False
        # Bilancio di massa
        derivative = total_inventory_change/dt
        #print(f"Inflow: {self.get_inflow()*dt}, Outflow: {total_outflow}, Derivative: {derivative}")
        self.outflow.append(total_outflow/dt)
        self.inflow.append(self.get_inflow())
        return total_outflow, derivative

    def update_inventory(self, a, dt, time):
        self.update_pumps(a, dt, time)
        for pump in self.pumps:
            pump['inventory_evolution'].append(pump['inventory'])
        """Restituisce l'inventario totale di tutte le pompe."""
        self.tritium_inventory = sum(pump['inventory'] for pump in self.pumps)
        #self.tritium_inventory = self.tritium_inventory * (1 - self.LAMBDA)
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
        self.active_pumps = []
        self.outflow = []
        self.inflow = []
        self.tritium_inventory = 0
    def calculate_inventory_derivative(self):
        dydt = self.inflow[-1]-self.outflow[-1]*(1+self.non_radioactive_loss)-self.tritium_inventory*self.LAMBDA
        return dydt
    def get_outflow(self):
        if self.outflow == []:
            return 0
        else:
            return self.outflow[-1]