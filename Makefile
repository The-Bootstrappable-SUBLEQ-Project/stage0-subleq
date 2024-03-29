.PHONY: noontide-emu check test slowtest slowcheck slowertest slowercheck
.DELETE_ON_ERROR:

ALL_DEPS := Examples/hello_world.bin Examples/hello_world.hex0 Examples/hello_world.hex1 Examples/hello_world.hex2 Examples/hello_world.lsq
ALL_DEPS += phase0-hex/hex0_monitor.bin phase0-hex/hex0_monitor.hex0 phase0-hex/hex0_monitor.lsq
ALL_DEPS += phase0-hex/hex1_monitor.bin phase0-hex/hex1_monitor.hex0 phase0-hex/hex1_monitor.hex1 phase0-hex/hex1_monitor.lsq
ALL_DEPS += phase0-hex/hex2_monitor.bin phase0-hex/hex2_monitor.hex0 phase0-hex/hex2_monitor.hex1 phase0-hex/hex2_monitor.hex2 phase0-hex/hex2_monitor.lsq
ALL_DEPS += phase0-hex/hex0.bin phase0-hex/hex0.hex0 phase0-hex/hex0.lsq
ALL_DEPS += phase0-hex/hex1.bin phase0-hex/hex1.hex0 phase0-hex/hex1.hex1 phase0-hex/hex1.lsq
ALL_DEPS += phase0-hex/hex2.bin phase0-hex/hex2.hex0 phase0-hex/hex2.hex1 phase0-hex/hex2.hex2 phase0-hex/hex2.lsq
ALL_DEPS += phase1-lsq-msq/lsq_to_hex.bin phase1-lsq-msq/lsq_to_hex.hex2 phase1-lsq-msq/lsq_to_hex.lsq
ALL_DEPS += Examples/test_jeq.bin Examples/test_str.bin Examples/test_print_qword.bin Examples/test_itoa.bin

all: $(ALL_DEPS)

%.bin: %.hex0
	sed 's/[;#].*$$//g' $< | xxd -r -p > $*.bin
	ls -al $*.bin

%.hex0: %.lsq High_Level_Prototypes/lsq_to_hex.py
	./High_Level_Prototypes/lsq_to_hex.py $< > $*.hex0

%.hex1: %.lsq High_Level_Prototypes/lsq_to_hex.py
	./High_Level_Prototypes/lsq_to_hex.py --hex-version 1 $< > $*.hex1

%.hex2: %.lsq High_Level_Prototypes/lsq_to_hex.py
	./High_Level_Prototypes/lsq_to_hex.py --hex-version 2 $< > $*.hex2

%.lsq: %.msq High_Level_Prototypes/msq_to_lsq.py
	./High_Level_Prototypes/msq_to_lsq.py $< > $*.lsq

noontide-emu: ../noontide-emu/Cargo.toml
	cd ../noontide-emu && cargo build --release

test: noontide-emu all
	cd Unit_Tests && pytest -v -n $$(nproc) || true

slowtest: noontide-emu all
	cd Unit_Tests && pytest -v --runslow -n $$(nproc) || true

slowertest: noontide-emu all
	cd Unit_Tests && pytest -v --runslower -n $$(nproc) || true

check: test
slowcheck: slowtest
slowercheck: slowertest
