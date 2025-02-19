import sys
import os

import openfc.simulate
import openfc.componentMap
import openfc.components.breedingBlanket
import openfc.components.fuelingSystem
import openfc.components.plasma
import openfc.components

I_startup = 1
I_res = I_startup
Nburn = 9.3e-7 * 0.7
TBR = 1.1
TBE = 0.1
TES_efficiency = 0.9
residence_time = 3600 #1 hour
TRU_residence_time = 12*3600 #12 hours
DIR = 0.3

TRU = openfc.components.component.Component("TRU", TRU_residence_time) #Tritium Recycling Unit
Plasma = openfc.components.plasma.Plasma("Plasma", Nburn, TBE, 0, 0)
BB = openfc.components.breedingBlanket.BreedingBlanket("BB", 3600 , Nburn, TBR=TBR)
FuelingSystem = openfc.components.fuelingSystem.FuelingSystem("Fueling System", Nburn, TBE, initial_inventory=I_startup)



#circuit: BB -> Fueling System -> Plasma -> TRU -> Fueling System 
#DIR: Plasma -> Fueling system 
port1 = Plasma.add_output_port("Plasma to Fuel System through DIR")
port2 = FuelingSystem.add_input_port("Fueling system from Plasma through DIR", incoming_fraction = DIR)
port3 = BB.add_output_port("BB to Fueling System")
port4 = FuelingSystem.add_input_port("Fueling System from BB", incoming_fraction=TES_efficiency)
port5 = FuelingSystem.add_output_port("Fueling System to Plasma")
port6 = Plasma.add_input_port("Plasma from Fueling System")
port7 = Plasma.add_output_port("Plasma to TRU")
port8 = TRU.add_input_port("TRU from Plasma", incoming_fraction = 1-DIR)
port9 = TRU.add_output_port("TRU to Fueling System")
port10 = FuelingSystem.add_input_port("Fueling System from TRU")


Map = openfc.componentMap.ComponentMap()
Map.add_component(FuelingSystem)
Map.add_component(BB)
Map.add_component(Plasma)
Map.add_component(TRU)

Map.connect_ports(BB, port3, FuelingSystem, port4)
Map.connect_ports(FuelingSystem, port5, Plasma, port6)
Map.connect_ports(Plasma, port1, FuelingSystem, port2)
Map.connect_ports(Plasma, port7, TRU, port8)
Map.connect_ports(TRU, port9, FuelingSystem, port10)

final_time = 2 * 3600 * 24 * 365 

Simulazione1= openfc.simulate.Simulate(1, final_time, I_res, Map, TBRr_accuraty = 1e-3, dt_max = 10000)
Simulazione1.run()