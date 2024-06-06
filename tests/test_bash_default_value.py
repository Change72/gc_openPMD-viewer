import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Batch Benchmark Generator Script')
    parser.add_argument('--bpfile', type=str, help='bp file path', default="")

    args = parser.parse_args()
    bp_file_path = args.bpfile

    print(bp_file_path)
    print(type(bp_file_path))
    print()