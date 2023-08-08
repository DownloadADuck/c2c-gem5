#!usr/bin/env bash

build/VEGA_X86/gem5.opt configs/example/c2ctest/hip_samples.py \
  --disk-image /home/lbertranalvarez/Work/fs/gpu/rocm42 \
  --kernel /home/lbertranalvarez/Work/fs/gpu/vmlinux-5.4.0-105-generic \
  --gpu-mmio-trace /home/lbertranalvarez/Work/fs/gpu/vega_mmio.log \
  -a PrefixSum \
  --num-compute-units 1
