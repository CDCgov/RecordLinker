#!/usr/bin/env python3
import argparse
import json

from ..scrambler import json as json_scrambler


def main() -> None:
    """
    Main entry point for the script.
    """
    parser = argparse.ArgumentParser(description="Scramble test data")
    parser.add_argument("--file", type=str, help="The file to load the test data from")
    args = parser.parse_args()

    if args.file.endswith(".json"):
        with open(args.file, "r") as f:
            data = json.load(f)

        scrambled_data = json_scrambler.scramble(data)

        # Save the scrambled data to a new file
        with open("scrambled_data.json", "w") as f:
            json.dump(scrambled_data, f, indent=4)

    else:
        # TODO: Convert CSV scrambler from expand_test_data.py
        print("File type not yet supported.")


if __name__ == "__main__":
    main()
