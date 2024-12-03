# gem5

## Get the code
```bash
git clone git@gite.lirmm.fr:lbertranalvarez/gem5.git
```

## Compilation
In `/gem5/.`

- Compile gem5 with X86 and the CHI protocol
- default binary
```bash
scons build/X86_CHI/gem5.opt PROTOCOL=CHI -j<num of cores>
```
- debug binary

```bash
scons build/X86_CHI/gem5.debug PROTOCOL=CHI -j<num of cores>
```
## Run

### Syscall
- Run the last **syscall** architecture (optional debug flag)
    - This is running a syscall emulation simulation running the Threads application.
```bash
build/X86_CHI/gem5.opt --debug-flags=RubyGenerated configs/slicc_interface/main.py
```

### Full-system
- Run a full-system simulation with a benchmark application from PARSEC the C2CI is calibrated (added delay for remote accesses)
    - Available benchmarks: *blackscholes, bodytrack, canneal, dedup, ferret, freqmine, raytrace, swaptions*

```bash
build/X86_CHI/gem5.opt configs/example/gem5_library/x86_c2c_kvm/C2C/timing-c2c-x86-ubuntu-boot-exit.py --benchmark <benchmark name> --size simsmall
```


