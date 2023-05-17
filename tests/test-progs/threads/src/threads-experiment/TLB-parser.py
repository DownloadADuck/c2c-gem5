import re


cpu0_itb = []
cpu0_dtb = []
cpu1_itb = []
cpu1_dtb = []
cpu2_itb = []
cpu2_dtb = []


cpu0_itb_tick = []
cpu0_dtb_tick = []
cpu1_itb_tick = []
cpu1_dtb_tick = []
cpu2_itb_tick = []
cpu2_dtb_tick = []


mode = "VA" # PA or VA
with open("./trace-TLB.txt", "r") as file:
   for line in file:
       #4637200500: system.cpu0.mmu.itb: Translated 0x7ffff72d6bb8 -> 0x12bbb8.
       match = re.match(r'(\S+): (\S+): Translated (\S+) -> (\S+).', line)
       if match:
           column0 = match.group(1)
           column1 = match.group(2)
           column2 = match.group(3)
           column3 = match.group(4)
          
           if mode == "PA":
               addr = column3
           else:
               addr = column2
              
           if  "system.cpu0.mmu.itb" in column1:
               #import pdb; pdb.set_trace()
               cpu0_itb.append(int(addr,0))
               cpu0_itb_tick.append(int(column0,0))
           elif "system.cpu0.mmu.dtb" in column1:
               #print(column1 + " " + column2)
               cpu0_dtb.append(int(addr,0))
               cpu0_dtb_tick.append(int(column0,0))
           elif "system.cpu1.mmu.itb" in column1:
               #print(column1 + " " + column2)
               cpu1_itb.append(int(addr,0))
               cpu1_itb_tick.append(int(column0,0))
           elif "system.cpu1.mmu.dtb" in column1:
               #print(column1 + " " + column2)               
               cpu1_dtb.append(int(addr,0))
               cpu1_dtb_tick.append(int(column0,0))
           elif "system.cpu2.mmu.itb" in column1:
               #print(column1 + " " + column2)
               cpu2_itb.append(int(addr,0))
               cpu2_itb_tick.append(int(column0,0))
           elif "system.cpu2.mmu.dtb" in column1:
               #print(column1 + " " + column2)               
               cpu2_dtb.append(int(addr,0))
               cpu2_dtb_tick.append(int(column0,0))          
       #else:
           #print("Invalid line:", line.strip())


#print (data_misses)
import numpy as np
from matplotlib import colors
import matplotlib.pyplot as plt


plt.subplot(211)
plt.plot(cpu0_dtb_tick, cpu0_dtb, linestyle = 'None', marker = '.', color = 'b')
plt.plot(cpu1_dtb_tick, cpu1_dtb, linestyle = 'None', marker = '.', color = 'g')
plt.plot(cpu2_dtb_tick, cpu2_dtb, linestyle = 'None', marker = '.', color = 'c')


plt.subplot(212)
plt.plot(cpu0_itb_tick, cpu0_itb, linestyle = 'None', marker = '.', color = 'b')
plt.plot(cpu1_itb_tick, cpu1_itb, linestyle = 'None', marker = '.', color = 'g')
plt.plot(cpu2_itb_tick, cpu2_itb, linestyle = 'None', marker = '.', color = 'c')
plt.show()
