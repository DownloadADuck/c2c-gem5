import sys

def extract_address_blocks(trace_file, address, output_file):
    with open(trace_file, 'r') as file:
        lines = file.readlines()
    
    capturing = False
    captured_blocks = []
    current_block = []

    for line in lines:
        if address in line:
            capturing = True
        if capturing:
            current_block.append(line)
        if 'next_state:' in line and capturing:
            captured_blocks.append(''.join(current_block))
            capturing = False
            current_block = []
    
    with open(output_file, 'w') as file:
        for block in captured_blocks:
            file.write(block + "\n")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python script.py <trace_file> <address> <output_file>")
        sys.exit(1)

    trace_file = sys.argv[1]
    address = sys.argv[2]
    output_file = sys.argv[3]

    extract_address_blocks(trace_file, address, output_file)
