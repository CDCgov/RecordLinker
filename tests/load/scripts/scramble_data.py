#!/usr/bin/env python3
import argparse
import json
import random
import sys
import time
import tracemalloc

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
    # Start memory tracking
    tracemalloc.start()
    start_time = time.time()
    mem_samples = []
    peak_samples = []
    timestamps = []

    if args.file.endswith(".json"):
        total_record_counter = 0
        first = True
        with open(args.file, "rb") as input_file, open("seed_data.json", "w") as output_file:
            clusters = ijson.items(input_file, "clusters.item", use_float=True)
            output_file.write('{"clusters": [\n')
            # Iterate over the clusters in the file
            for cluster in clusters:
                # Take memory snapshot
                current, peak = tracemalloc.get_traced_memory()
                mem_samples.append(current)
                peak_samples.append(peak)
                timestamps.append(time.time() - start_time)
                if random.random() < 0.66:  # Scramble some of the available clusters
                    scrambled_cluster = json_scrambler.scramble(cluster)
                    if not first:
                        output_file.write(",\n")
                    total_record_counter += len(scrambled_cluster["records"])
                    if total_record_counter % 10000 == 0:
                        print(
                            f"Processed {total_record_counter} records so far...",
                            file=sys.stderr,
                            flush=True,
                        )

                    json.dump(scrambled_cluster, output_file, indent=4)
                    output_file.flush()
                    first = False
                # Only scramble a subset of the clusters
                if total_record_counter >= args.max_seed_records:
                    break
            output_file.write("\n]}\n")
            output_file.flush()

            # Final memory snapshot
        current, peak = tracemalloc.get_traced_memory()
        mem_samples.append(current)
        timestamps.append(time.time() - start_time)
        tracemalloc.stop()

        with open("memory_trace.csv", "w") as f:
            f.write("time_seconds,memory_bytes,peaks\n")
            for t, m, p in zip(timestamps, mem_samples, peak_samples):
                f.write(f"{t},{m},{p}\n")

    else:
        # TODO: Convert CSV scrambler from expand_test_data.py
        print("File type not yet supported.")


if __name__ == "__main__":
    main()
