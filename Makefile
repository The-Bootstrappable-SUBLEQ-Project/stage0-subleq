ALL_DEPS := phase0-hex/hex0_monitor.bin phase0-hex/hex0_monitor.hex0 phase0-hex/hex0_monitor.lsq
ALL_DEPS += Examples/hello_world.bin Examples/hello_world.hex0 Examples/hello_world.hex1 Examples/hello_world.hex2 Examples/hello_world.lsq

all: $(ALL_DEPS)

phase0-hex/hex0_monitor.bin: phase0-hex/hex0_monitor.hex0
	sed 's/[;#].*$$//g' phase0-hex/hex0_monitor.hex0 | xxd -r -p > phase0-hex/hex0_monitor.bin
	ls -al phase0-hex/hex0_monitor.bin

phase0-hex/hex0_monitor.hex0: High_Level_Prototypes/lsq_to_hex.py phase0-hex/hex0_monitor.lsq
	./High_Level_Prototypes/lsq_to_hex.py phase0-hex/hex0_monitor.lsq > phase0-hex/hex0_monitor.hex0

phase0-hex/hex0_monitor.lsq: High_Level_Prototypes/msq_to_lsq.py phase0-hex/hex0_monitor.msq
	./High_Level_Prototypes/msq_to_lsq.py phase0-hex/hex0_monitor.msq > phase0-hex/hex0_monitor.lsq

Examples/hello_world.bin: Examples/hello_world.hex0
	sed 's/[;#].*$$//g' Examples/hello_world.hex0 | xxd -r -p > Examples/hello_world.bin
	ls -al Examples/hello_world.bin

Examples/hello_world.hex0: High_Level_Prototypes/lsq_to_hex.py Examples/hello_world.lsq
	./High_Level_Prototypes/lsq_to_hex.py Examples/hello_world.lsq > Examples/hello_world.hex0

Examples/hello_world.hex1: High_Level_Prototypes/lsq_to_hex.py Examples/hello_world.lsq
	./High_Level_Prototypes/lsq_to_hex.py --hex-version 1 Examples/hello_world.lsq > Examples/hello_world.hex1

Examples/hello_world.hex2: High_Level_Prototypes/lsq_to_hex.py Examples/hello_world.lsq
	./High_Level_Prototypes/lsq_to_hex.py --hex-version 2 Examples/hello_world.lsq > Examples/hello_world.hex2

Examples/hello_world.lsq: High_Level_Prototypes/msq_to_lsq.py Examples/hello_world.msq
	./High_Level_Prototypes/msq_to_lsq.py Examples/hello_world.msq > Examples/hello_world.lsq