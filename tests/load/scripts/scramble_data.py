#!/usr/bin/env python3
import argparse
import json
import random

import ijson

from ..scrambler import json as json_scrambler


def main() -> None:
    """
    Main entry point for the script.
    """
    parser = argparse.ArgumentParser(description="Scramble test data")
    parser.add_argument(
        "--file", type=str, help="The file to load the test data from", required=True
    )
    parser.add_argument(
        "--max-seed-records",
        type=int,
        default=25,
        help="The maximum number of records to generate for seeding",
        required=True,
    )

    args = parser.parse_args()

    if args.file.endswith(".json"):
        total_record_counter = 0
        first = True
        with open(args.file, "rb") as input_file, open("seed_data.json", "w") as output_file:
            clusters = ijson.items(input_file, "clusters.item", use_float=True)
            output_file.write('{"clusters": [\n')
            # Iterate over the clusters in the file
            for cluster in clusters:
                if random.random() < 0.66:  # Scramble some of the available clusters
                    scrambled_cluster = json_scrambler.scramble(cluster)
                    if not first:
                        output_file.write(",\n")
                    total_record_counter += len(scrambled_cluster["records"])
                    json.dump(scrambled_cluster, output_file, indent=4)
                    first = False
                # Only scramble a subset of the clusters
                if total_record_counter >= args.max_seed_records:
                    break
            output_file.write("\n]}\n")

    else:
        # TODO: Convert CSV scrambler from expand_test_data.py
        print("File type not yet supported.")


if __name__ == "__main__":
    main()
