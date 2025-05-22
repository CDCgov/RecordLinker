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
        cluster_list = []
        total_record_counter = 0
        with open(args.file, "rb") as f:
            clusters = ijson.items(f, "clusters.item", use_float=True)
            # Iterate over the clusters in the file
            for cluster in clusters:
                if random.random() < 0.66:  # Scramble some of the available clusters
                    scrambled_cluster = json_scrambler.scramble(cluster)
                    cluster_list.append(scrambled_cluster)
                    total_record_counter += len(scrambled_cluster["records"])
                # Only scramble a subset of the clusters
                if total_record_counter >= args.max_seed_records:
                    break
        # Write the scrambled clusters to a new file
        with open("seed_data.json", "w") as f:
            json.dump({"clusters": cluster_list}, f, indent=4)

    else:
        # TODO: Convert CSV scrambler from expand_test_data.py
        print("File type not yet supported.")


if __name__ == "__main__":
    main()
