import sys

def extract_unique_events(input_file, output_file):
    unique_events = set()  # Use a set to store unique events

    try:
        with open(input_file, 'r') as file:
            for line in file:
                if "Time:" in line:
                    # Extract the part of the line that contains the event description
                    parts = line.split('event: ')
                    if len(parts) > 1:
                        event_part = parts[1].split(',')[0]  # Get the event name before the comma
                        unique_events.add(event_part.strip())  # Add to the set, stripping any extra whitespace

        # Writing the unique events to the output file
        with open(output_file, 'w') as outfile:
            for event in sorted(unique_events):  # Write sorted events for better readability
                outfile.write(event + '\n')

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <input_file> <output_file>")
    else:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
        extract_unique_events(input_file, output_file)
        print(f"Unique events have been written to {output_file}")

