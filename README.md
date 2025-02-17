# gem5

## Get the code
```bash
git clone git@gite.lirmm.fr:adac/gem5.git
```
## Docker image
### Build
- If using apple silicon, modify the *dockerfile* ubuntu import by uncommenting the appropriate line.

```bash
docker build -t c2c-gem5 .
```
### Run
```bash
docker run -it c2c-gem5 /bin/bash
```
Once in the docker environment, you can proceed to the compilation and run.

## Compilation
> The current version of c2c-gem5 can cause errors when adding delay to the C2C Link. For this reason, before compiling, make sure that you set the C2C Link delay to its appropriate value, depending on what you want to run (i.e., syscall emulation or full-system PARSEC workloads). See further in the **Run** section.

In `/gem5/.`

- Compile gem5 with X86 and the CHI protocol
- default binary
```bash
scons build/X86_CHI/gem5.opt PROTOCOL=CHI -j$(nproc)
```
- debug binary

```bash
scons build/X86_CHI/gem5.debug PROTOCOL=CHI -j$(nproc)
```
## Run

### Syscall
- Run the last **syscall** architecture (optional debug flag)
    - This is running a syscall emulation simulation running the Threads application.
    - This script doesn't complete if there is delay in the C2C link (fix in progress). To verify or change the value, open the script in `./src/mem/ruby/protocol/chi/CHI-interface.sm` and change de value on line 7 to 0. 
    - If changes are made, you will need to compile gem5 again.
```bash
build/X86_CHI/gem5.opt --debug-flags=RubyGenerated configs/slicc_interface/main.py
```

### Full-system
- Run a full-system simulation with a benchmark application from PARSEC the C2CI is calibrated (added delay for remote accesses)
    - Available benchmarks: *blackscholes, bodytrack, canneal, dedup, ferret, freqmine, raytrace, swaptions*
    - Not all benchmark run when using 0 delay on the C2C link. Refer to the explanation in the Syscall emulation mode to change the value of `c2c_link_latency` to 685.

```bash
build/X86_CHI/gem5.opt configs/example/gem5_library/x86_c2c_kvm/C2C/timing-c2c-x86-ubuntu-boot-exit.py --benchmark <benchmark name> --size simsmall
```


