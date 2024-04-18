import sys

def process_trace_file(input_file, output_file):
    try:
        with open(input_file, 'r') as file, open(output_file, 'w') as outfile:
            for line in file:
                if "Time:" in line:
                    parts = line.split()
                    cleaned_line = ' '.join(parts[1:]) + '\n'  # Add newline for writing to file
                    outfile.write(cleaned_line)
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <input_file> <output_file>")
    else:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
        process_trace_file(input_file, output_file)
        print(f"Processed lines have been written to {output_file}")
