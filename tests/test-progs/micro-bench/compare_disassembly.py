import re
import sys

def parse_file(filename):
    instructions = []
    with open(filename, 'r') as f:
        for line in f:
            match = re.search(r'^\s*(?P<address>[0-9a-f]+):\s*(?P<instruction>[0-9a-f ]+)\s*(?P<comment>.*)$', line)
            if match:
                address = int(match.group('address'), 16)
                instruction = match.group('instruction').replace(' ', '')
                instructions.append((address, instruction))
    return instructions

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: python compare_disassembly.py file1 file2')
        sys.exit(1)

    file1 = sys.argv[1]
    file2 = sys.argv[2]

    instructions1 = parse_file(file1)
    instructions2 = parse_file(file2)

    overlap = False
    for i, (address1, instruction1) in enumerate(instructions1):
        if i >= len(instructions2):
            break
        address2, instruction2 = instructions2[i]
        if address1 == address2:
            print(f'Error: instructions overlap at address 0x{address1:x}')
            overlap = True

    if overlap:
        sys.exit(1)
    else:
        print('Instructions do not overlap.')

    # Print highest and lowest memory addresses of each input file
    addresses1 = [addr for addr, _ in instructions1]
    addresses2 = [addr for addr, _ in instructions2]
    print(f'{file1}: lowest address = 0x{min(addresses1):x}, highest address = 0x{max(addresses1):x}')
    print(f'{file2}: lowest address = 0x{min(addresses2):x}, highest address = 0x{max(addresses2):x}')