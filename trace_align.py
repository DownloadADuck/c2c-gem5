import sys
import os

def compare_trace_files(failing_file_path, working_file_path):
    with open(failing_file_path, 'r') as failing_file, open(working_file_path, 'r') as working_file:
        matching_lines = 0
        total_lines = 0

        for failing_line, working_line in zip(failing_file, working_file):
            total_lines += 1
            if failing_line == working_line:
                matching_lines += 1

        match_percentage = (matching_lines / total_lines) * 100 if total_lines > 0 else 0

        failing_file_size = os.path.getsize(failing_file_path)
        working_file_size = os.path.getsize(working_file_path)
        coverage_estimate = (failing_file_size / working_file_size) * 100 if working_file_size > 0 else 0

        return match_percentage, coverage_estimate

def main():
    if len(sys.argv) != 3:
        print("Usage: python compare_traces.py <failing_trace_file> <working_trace_file>")
        sys.exit(1)

    failing_file_path = sys.argv[1]
    working_file_path = sys.argv[2]

    match_percentage, coverage_estimate = compare_trace_files(failing_file_path, working_file_path)

    print(f"Match Percentage: {match_percentage:.2f}%")
    print(f"Coverage Estimate: {coverage_estimate:.2f}%")

if __name__ == "__main__":
    main()
