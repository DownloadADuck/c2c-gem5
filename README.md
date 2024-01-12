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

- Run the last architecture (optional tgen debug flag)
```bash
build/X86_CHI/gem5.opt --debug-flags=TrafficGen configs/interface_bridge/tgen_arm.py
```
- Run the `two_HNFs` working architecture (working memory region setup)
```bash
build/X86_CHI/gem5.opt --debug-flags=TrafficGen configs/two_HNFs/tgen_arm.py
```
