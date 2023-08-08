#!usr/bin/env bash

# Running the trace based simulation
# Using CHI and modified version of se.py

./build/C2C_X86/gem5.opt \
    --debug-flags=TrafficGen \
    configs/example/tgen_se.py \
    --ruby \
    --caches \
    --topology=Pt2Pt \
    --num-cpus=2 \
    --cmd=tests/test-progs/hello/bin/x86/linux/hello