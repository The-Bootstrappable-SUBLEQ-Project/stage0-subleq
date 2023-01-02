all: phase0-hex/hex0_monitor.bin phase0-hex/hex0_monitor.hex0 phase0-hex/hex0_monitor.lsq

phase0-hex/hex0_monitor.bin: phase0-hex/hex0_monitor.hex0
	sed 's/[;#].*$$//g' phase0-hex/hex0_monitor.hex0 | xxd -r -p > phase0-hex/hex0_monitor.bin
	ls -al phase0-hex/hex0_monitor.bin

phase0-hex/hex0_monitor.hex0: High_Level_Prototypes/lsq_to_hex.py phase0-hex/hex0_monitor.lsq
	./High_Level_Prototypes/lsq_to_hex.py phase0-hex/hex0_monitor.lsq > phase0-hex/hex0_monitor.hex0

phase0-hex/hex0_monitor.lsq: High_Level_Prototypes/msq_to_lsq.py phase0-hex/hex0_monitor.msq
	./High_Level_Prototypes/msq_to_lsq.py phase0-hex/hex0_monitor.msq > phase0-hex/hex0_monitor.lsq