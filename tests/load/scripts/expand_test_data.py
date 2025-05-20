#!/usr/bin/env python3
import argparse
import json

from scrambler.json import JSONScrambler


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

    elif args.file.endswith(".csv"):
        print("CSV file format is not supported yet")

    # Pass to the scrambler
    # scrambler = Scrambler(data, relevant_fields)
    # randomly select fields to scramble
    #     fields_to_scramble = scrambler._get_scramblable_fields()
    # scramble the fields
    #     scrambled_data = scrambler.apply_field_scrambling()
    # shuffle the order of the records
    ALGORITHM_RELEVANT_COLUMNS = ["FIRST", "LAST"]
    for cluster in data["clusters"]:
        for record in cluster["records"]:
            scrambled_data = JSONScrambler(
                record, relevant_fields=ALGORITHM_RELEVANT_COLUMNS
            ).scramble()


if __name__ == "__main__":
    main()
