#!/bin/bash

# Run the gem5 sim
build/X86_CHI/gem5.opt \
	--debug-flags=RubyGenerated \
	--debug-start=865600000000 \
	configs/example/gem5_library/x86_c2c_kvm/create-checkpoint-x86-ubuntu-boot-exit.py > \
	switch_output.yaml

# Check exit status 
if  [ $? -eq 0 ]; then
	echo "Simulation completed successfully"
else
	echo "Simulation crashed or ended with an error"
fi

# Send a notification email
curl -s \
	--form-string "token=aszmadux5dih8h9q1dw653wtu21n7j" \
	--form-string "user=uaieu5ay7z5sooib15dhqwithhg8je" \
	--form-string "message=Simulation ended." \
	https://api.pushover.net/1/messages.json
#python3 send_email.py
