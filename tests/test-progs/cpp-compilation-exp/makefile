
AS  = as
CC  = gcc
CXX = g++
LD  = ld
OBJCOPY = objcopy
OBJDUMP = objdump

OUTDIR1 = ./build1
OUTDIR2 = ./build2

ASFLAGS =
GFLAGS 	=
CFLAGS  = -nostdlib
LDFLAGS = --gc-sections -nostdlib

all: hello1 hello2

hello1:
	mkdir -p $(OUTDIR1)
	$(AS) startup.S -o $(OUTDIR1)/startup.o $(GFLAGS) $(ASFLAGS)
	$(CC) main.c    -o $(OUTDIR1)/main.o    $(GFLAGS) $(CFLAGS) -c -s
	$(LD)  $(OUTDIR1)/main.o $(OUTDIR1)/startup.o -o $(OUTDIR1)/hello1.elf $(GFLAGS) $(LDFLAGS) -T linker.ld --defsym=startaddr=0x400680
	$(OBJCOPY) $(OUTDIR1)/hello1.elf -O binary $(OUTDIR1)/hello1.bin
	$(OBJCOPY) $(OUTDIR1)/hello1.elf -O ihex $(OUTDIR1)/hello1.hex
	$(OBJDUMP) -S --disassemble $(OUTDIR1)/hello1.elf > $(OUTDIR1)/hello1.dump

hello2:
	mkdir -p $(OUTDIR2)
	$(AS) startup.S -o $(OUTDIR2)/startup.o $(GFLAGS)
	$(CC) main.c    -o $(OUTDIR2)/main.o    $(GFLAGS) $(CFLAGS) -c -s
	$(LD)  $(OUTDIR2)/main.o $(OUTDIR2)/startup.o -o $(OUTDIR2)/hello2.elf $(GFLAGS) $(LDFLAGS) -T linker.ld --defsym=startaddr=0x10400680
	$(OBJCOPY) $(OUTDIR2)/hello2.elf -O binary $(OUTDIR2)/hello2.bin
	$(OBJCOPY) $(OUTDIR2)/hello2.elf -O ihex $(OUTDIR2)/hello2.hex
	$(OBJDUMP) -S --disassemble $(OUTDIR2)/hello2.elf > $(OUTDIR2)/hello2.dump

.PHONY: clean
clean:
	rm -rf $(OUTDIR1)
	rm -rf $(OUTDIR2)