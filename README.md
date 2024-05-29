# gem5

In `/gem5/.`

- Checkout on the last branch
```bash
git checkout bridge-ports
```

- Compile gem5 with X86 and the CHI protocol
- default binary
```bash
scons build/X86_CHI/gem5.opt --default=X86 PROTOCOL=CHI -j<num of cores>
```
- debug binary

```bash
scons build/X86_CHI/gem5.debug --default=X86 PROTOCOL=CHI -j<num of cores>
```

- Run the last **syscall** architecture (optional debug flag)
```bash
build/X86_CHI/gem5.opt --debug-flags=RubyGenerated configs/slicc_interface/main.py
```
- Run the last **full-system** architecture
```bash
build/X86_CHI/gem5.opt configs/example/gem5_library/x86-chi-ubuntu-boot-exit.py
```
## Checkpoint with traces

- Run the FS simulation with the **C2cTraces** debug flag
```bash
build/X86_CHI/gem5.opt --debug-flags=C2cTraces --debug-start=<start_tick> configs/example/gem5_library/x86_c2c_kvm/no-checkpoint-x86-ubuntu-boot-exit.py > trace.log
```
- Filter the traces to remove IFETCH
```bash
python3 icache_trace_filter.py <input_log_file> <output_log_file>```

- Run the python parser with the previous output log file as input to generate the traces 
```bash
build/X86_CHI/gem.opt config/traces/checkpoint_trace.py --log-file <output_log_file>
```
- Run the simulation with the two trace files (optional debug flag)
```bash
build/X86_CHI/gem5.opt --debug-flags=RubyGenerated config/two_tgens_se_c2c/main.py
```
