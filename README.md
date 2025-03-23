# c2c-gem5
This project is an extension of gem5 v22.01 allowing the modeling of **two chips interconnected and extending their cache coherence**. It allows to run syscall emulation simulations of user application benchmarks, trace injection simulation using gem5's tgens, as well as full-system simulations running workloads from the PARSEC suite. This work is explained in the following paper: [c2c-gem5: Full System Simulation of Cache-Coherent Chip-to-Chip Interconnects](https://hal.science/hal-04993538/).

This project includes the tools to: 
- Compile and run a docker image to prepare the environment for gem5
- Compile gem5 with the extended version of the ARM CHI protocol 
- Run the *threads* application in syscall emulation mode
- Run *PARSEC* workloads in full-system mode

## Installation & setup 
### Code
- Get the code from this repository
- Checkout to the main branch
```bash
git clone https://gite.lirmm.fr/adac/c2c-gem5.git
git checkout main
```
### Docker image
#### Build
- Inside `c2c-gem5/`
- If using apple silicon, modify the *dockerfile* ubuntu import by uncommenting the appropriate line and commenting the original `FROM` statement

```dockerfile
# Ubuntu
FROM ubuntu:20.04

# If using apple silicon
#FROM --platform=linux/amd64 ubuntu:20.04
```

```bash
docker build -t c2c-gem5 .
```
#### Run
```bash
docker run -it c2c-gem5 /bin/bash
```
Once in the docker environment, you can proceed to the compilation and run.

## Compilation
> 🚨 The current version of c2c-gem5 can cause errors when adding delay to the C2C Link. For this reason, before compiling, make sure that you set the C2C Link delay to its appropriate value, depending on what you want to run (i.e., syscall emulation or full-system PARSEC workloads). See further in the **Run** section.

In `/gem5/.`

- Compile gem5 with X86 and the CHI protocol
- You can select the desired binary type with the `.opt` or `.debug` extensions 
```bash
scons build/X86_CHI/gem5.opt PROTOCOL=CHI -j$(nproc)
```
```bash
scons build/X86_CHI/gem5.debug PROTOCOL=CHI -j$(nproc)
```
## Run
### Syscall
- Run the **syscall** simulation
    - This is a syscall emulation simulation running the Threads application.
    - This script doesn't complete if there is delay in the C2C link (fix in progress). To verify or change the value, open the script in `./src/mem/ruby/protocol/chi/CHI-interface.sm` and change de value on line 7 to 0. 
    - If changes are made, you will need to compile gem5 again.

To run the simulation (with the optional debug flag)
```bash
build/X86_CHI/gem5.opt --debug-flags=RubyGenerated configs/slicc_interface/main.py
```

### Full-system
- Run a full-system simulation with a benchmark application from PARSEC. The C2CI is calibrated (added delay for remote accesses)
    - Available benchmarks: *blackscholes, bodytrack, canneal, dedup, ferret, freqmine, raytrace, swaptions*
    - Not all benchmark run when using 0 delay on the C2C link. Refer to the explanation in the Syscall emulation mode to change the value of `c2c_link_latency` to 685.
    - Benchmarks have been tested only for the *simsmall* size and may not run to completion with bigger sizes. 
```bash
build/X86_CHI/gem5.opt configs/example/gem5_library/x86_c2c_kvm/C2C/noncaching-c2c.py --benchmark <benchmark name> --size simsmall
```
Exemple to run the canneal benchmark:
```bash
build/X86_CHI/gem5.opt configs/example/gem5_library/x86_c2c_kvm/C2C/noncaching-c2c.py --benchmark canneal --size simsmall
```
**🚨 Simulations can take from 1h upwards to 15h. We recommend running them in a *tmux* session or similar.**

- This configuration script uses the *gem5 standard library* and its resources. It should download the needed resources automatically in your `~/.cache/gem5` folder. If you want to run multiple simulations in parallel, you will need to use multiple copies of the ressources. You can impose a resource folder to gem5 as follows: 
```bash
GEM5_RESOURCE_DIR=~/.cache/gem5/ build/X86_CHI/gem5.opt configs/example/gem5_library/x86_c2c_kvm/C2C/noncaching-c2c.py --benchmark canneal --size simsmall
```

## Debug
This project is in development and is unstable. Some benchmark applications will run and some will cause issues. This section describe the most common **runtime** issues and where to look at. 

### Invalid transition
When running a wide array of benchmarks, the most probable runtime error is an invalid transition. This means that a controller of the architecture received a message that was not expected at that time. This will mostly impact the C2CI controllers. 

The most effective way of understanding the issue is to generate a trace of the transitions. You will need to start the trace a couple of millions of ticks before the error. 

```bash
build/X86_CHI/gem5.opt --debug-flags=RubyGenerated --debug-start=<your tick number minus a value> configs/example/gem5_library/x86_c2c_kvm/C2C/noncaching-c2c.py --benchmark canneal --size simsmall > invalid_transition.log
```
## Contacts
Luis Bertran Alvarez - [luis.bertran-alvarez@lirmm.fr](mailto:luis.bertran-alvarez@lirmm.fr)

David Novo - [david.novo@lirmm.fr](mailto:david.novo@lirmm.fr)
