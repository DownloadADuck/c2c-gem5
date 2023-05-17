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


ref_addr = "0x1b9980"
cache_line_state = {"system.cpu0.l1d": "INIT", "system.cpu1.l1d": "INIT", "system.cpu2.l1d": "INIT", "system.cpu0.l2": "INIT", "system.cpu1.l2": "INIT", "system.cpu2.l2": "INIT", "system.ruby.hnf.cntrl": "INIT"}


init_req = 0
tab = ""
prev_addr = ""


with open("./trace-ruby.txt", "r") as file:
   for line in file:
       #479406000: system.cpu2.l2: [Cache_Controller 8], Time: 958812, state: BUSY_BLKD, event: SnpRespData_I_PD, addr: 0x1c4b80
       match = re.match(r'(\S+): (\S+): \[Cache_Controller .*? state: (\S+), event: (\S+), addr: (\S+)', line)


       #479382000: system.ruby.hnf.cntrl.snpOut: Enqueue arrival_time: 479382500, Message: [CHIRequestMsg: addr = [0x1c4b80, line 0x1c4b80] accAddr = [0x1c4b80, line 0x1c4b80] accSize = 64 type = SnpUniqueFwd requestor = Cache-9 fwdRequestor = Cache-8 dataToFwdRequestor = 0 retToSrc = 0 allowRetry = 0 Destination = [NetDest (20)  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  - 0 0 0 0 0 0 1 0 0 0  - 0  - 0  -  - ] seqReq = 0x422c9f10 isSeqReqValid = 1 is_local_pf = 0 is_remote_pf = 0 usesTxnId = 0 txnId = [0x0, line 0x0] MessageSize = Control ]
       match2 = re.match(r'(\S+): (\S+).snpOut: .*? addr = \[(\S+),.*?\[NetDest \(20\)  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  - (\S) (\S) (\S) (\S) (\S) (\S) (\S) (\S) (\S) (\S)  - 0  - 0  -  - \] ', line)
      
       # 479392500: system.cpu0.l2: next_state: I
       match3 = re.match(r'(\S+): (\S+): next_state: (\S+)', line)
      
       # 479427000: system.cpu2.l1i.triggerQueue: Message: [Cache_TriggerMsg: addr = [0x2d00, line 0x2d00] usesTxnId = 0 from_hazard = 0 ]
       match4 = re.match(r'(\S+): (\S+): Message: \[Cache_TriggerMsg: addr = \[(\S+), line (\S+)\] usesTxnId = 0 from_hazard = 0 \]', line)
      
       if match4:
           controller = match4.group(2)
           prev_addr = match4.group(4)
      
       if match3:
           controller = match3.group(2)
           state = match3.group(3)
           if prev_addr == ref_addr:
               if controller != "system.cpu0.l1i" and controller != "system.cpu1.l1i" and controller != "system.cpu2.l1i":
                   cache_line_state[controller] = state
       if match2:
           dst = ""
           tick = match2.group(1)
           src = match2.group(2)
           addr = match2.group(3)
           cpu0_l1d = match2.group(5)
           cpu1_l1d = match2.group(7)
           cpu2_l1d = match2.group(9)
           cpu0_l2  = match2.group(10)
           cpu1_l2  = match2.group(11)
           cpu2_l2  = match2.group(12)
           #print (match2.group(1) + " " + match2.group(2) + " " + match2.group(3) + " " + match2.group(5) + " " + match2.group(7) + " " + match2.group(8) + " " + match2.group(9) + " " + match2.group(10)+ " " + match2.group(11))
           if '1' in cpu0_l1d:
               dst = "system.cpu0.l1d"
           elif '1' in cpu1_l1d:
               dst = "system.cpu1.l1d"
           elif '1' in cpu2_l1d:
               dst = "system.cpu2.l1d"
           elif '1' in cpu0_l2:
               dst = "system.cpu0.l2"
           elif '1' in cpu1_l2:
               dst = "system.cpu1.l2"
           elif '1' in cpu2_l2:
               dst = "system.cpu2.l2"
           else:
               print ("Error: no destination found")
          
           if  ref_addr in addr:
               print (tab + src + " sends snoop to "+ dst)     
          
       if match:
           tick = match.group(1)
           controller = match.group(2)
           state = match.group(3)
           event = match.group(4)
           addr = match.group(5)
          
           if  ref_addr in addr:
               #import pdb; pdb.set_trace()
               cache_line_state[controller] = state
              
               if "Store" in event:
                   print (tab + "----> " + controller + " request Write on " + addr)
                   print (str(cache_line_state))   
                   init_req = init_req + 1 
                   tab = tab + "  " 
               if init_req > 0:   
                   if ("AllocRequest" in event): 
                       print (tab + controller + " access on " + addr )
                       print (str(cache_line_state))
                   if ("StoreHit" in event): 
                       print (tab + controller + " hits on " + addr)   
                       init_req = init_req - 1
                       tab = tab[:-2]
                   elif ("ReadMissPipe" in event): 
                       print (tab + controller + " misses on " + addr)
                   elif ("Final" in event):
                       if "l1d" in controller:
                           tab = tab[:-2]
                           print (tab + "<---- " + controller)
           elif "system.cpu0.mmu.dtb" in addr:
               #print(column1 + " " + column2)
               cpu0_dtb.append(int(tick,0))
               cpu0_dtb_tick.append(int(tick,0))
                    
       #else:
           #print("Invalid line:", line.strip())
