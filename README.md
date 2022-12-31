# stage0-subleq
A place for public review of the SUBLEQ port of stage0. The goal is to bootstrap a GNU/Linux system on an emulated/physical Noontide SUBLEQ Computer.

# Manually written files
### **Do not trust any files of this category without manually reviewing them first!**
### High Level Prototypes/msq_to_lsq.py
Expands an msq (Macro SUBLEQ) program to an lsq (Lesser SUBLEQ) program
### High Level Prototypes/lsq_to_hex.py
Assembles an lsq (Lesser SUBLEQ) program and outputs hex{0,1,2} files (TODO)
### phase0-hex/hex0_monitor.msq
This is just like a regular hex0_monitor, except it copies the assembled file to 0x0 of the memory and executes it. This is because we don't have any filesystem support at this stage.

# Automatically generated files
### **Do not trust any files of this category without either manually reviewing or regenerating them under a trusted environment first!**

### phase0-hex/hex0_monitor.lsq
This file can be regenerated via the following methods:
1. Running `./High\ Level\ Prototypes/msq_to_lsq.py phase0-hex/hex0_monitor.msq > phase0-hex/hex0_monitor.lsq` on a Python-enabled+Trusted computer
2. Using the SUBLEQ implementation of msq_to_lsq to expand it (TODO)
3. Converting it yourself manually (See High Level Prototypes/msq_to_lsq.py for what each instruction should do)