# gem5

In `/gem5/.`

Compile gem5 with C2C protocol:
```bash
scons build/C2C_X86/gem5.opt --default=X86 PROTOCOL=C2C -j12
```

Run the C2C testing script :

```bash
source c2c-interface-testing.sh
```
