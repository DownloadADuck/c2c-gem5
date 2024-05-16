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