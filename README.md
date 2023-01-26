# stage0-subleq
A place for public review of the SUBLEQ port of stage0. The goal is to bootstrap a GNU/Linux system on an emulated/physical Noontide SUBLEQ Computer.

# Manually written files
### **Do not trust any files of this category without manually reviewing them first!**
### High Level Prototypes/msq_to_lsq.py
Expands an msq (Macro SUBLEQ) program to an lsq (Lesser SUBLEQ) program
### High Level Prototypes/lsq_to_hex.py
Assembles an lsq (Lesser SUBLEQ) program and outputs hex0, hex1, or hex2 files
### phase0-hex/hex0.msq
Takes a hex0 program from serial input and outputs the assembled file into serial output.
### phase0-hex/hex0_monitor.msq
This is just like a regular hex0_monitor, except it copies the assembled file to 0x0 of the memory and executes it. This is because we don't have any filesystem support at this stage.
### Examples/hello_world.msq
This prints the string "Hello, world!" and then proceeds to halt the CPU.

# Automatically generated files
### **Do not trust any files of this category without either manually reviewing or regenerating them under a trusted environment first!**

### Examples/hello_world.lsq
This file can be regenerated via the following methods:
1. Running `make -B Examples/hello_world.lsq` on a Makefile-enabled + Python-enabled + Trusted computer
2. Running `./High_Level_Prototypes/msq_to_lsq.py Examples/hello_world.msq > Examples/hello_world.lsq` on a Python-enabled + Trusted computer
3. Using the SUBLEQ implementation of msq_to_lsq to expand it (TODO)
4. Converting it yourself manually (See High_Level_Prototypes/msq_to_lsq.py for what each instruction should do)

### Examples/hello_world.hex$HEX_VER
This file can be regenerated via the following methods:
1. Running `make -B Examples/hello_world.hex$HEX_VER` on a Makefile-enabled + Python-enabled + Trusted computer
2. Running `./High_Level_Prototypes/lsq_to_hex.py --hex-version $HEX_VER Examples/hello_world.lsq > Examples/hello_world.hex$HEX_VER` on a Python-enabled + Trusted computer
3. Using the SUBLEQ implementation of lsq_to_hex to assemble it (TODO)
4. Converting it yourself manually (See High_Level_Prototypes/lsq_to_hex.py for what each instruction should do)

### Examples/hello_world.bin
This file can be regenerated via the following methods:
1. Running `make -B Examples/hello_world.bin` on a Makefile-enabled + Trusted POSIX computer
2. Running `sed 's/[;#].*$//g' Examples/hello_world.hex0 | xxd -r -p > Examples/hello_world.bin` on a Trusted POSIX computer (You might need to escape the $)
3. Running `noontide-emu -b Examples/hello_world.hex$HEX_VER phase0-hex/hex$HEX_VER > Examples/hello_world.bin` on a Trusted computer with noontide-emu available
4. Converting it yourself manually

Programs such as phase0-hex/hex0_monitor and phase0-hex/hex0 can similarly be regenerated using the methods above.