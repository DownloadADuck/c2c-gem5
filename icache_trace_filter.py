import sys

def filter_log(input_file, output_file):
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        write_line = False
        for line in infile:
            if 'icache' in line:
                write_line = False
            elif 'dcache' in line:
                write_line = True
            if write_line:
                outfile.write(line)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 icache_trace_filter.py <input_log_file> <output_log_file")
        sys.exit(1)

    input_log_file = sys.argv[1]
    output_log_file = sys.argv[2]

    filter_log(input_log_file, output_log_file)