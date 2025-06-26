#!/usr/bin/env python
"""
scripts/seed_data.py
~~~~~~~~~~~~~~~~~~~~

Script to send data to the /seed endpoint in the RecordLinker project.
"""

import argparse
import itertools
import json
import sys
import typing
import urllib.error
import urllib.request

import ijson


def batched_iterator(iterator: typing.Iterator, batch_size: int) -> typing.Iterator:
    ""
    while True:
        batch = list(itertools.islice(iterator, batch_size))
        if not batch:
            break
        yield batch


def seed_data(base_url: str, data: dict) -> None:
    ""
    req = urllib.request.Request(
        url=f"{base_url}/seed",
        data=json.dumps(data).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as response:
            if response.status != 201:
                raise Exception(f"Request failed with status {response.status}")
    except urllib.error.HTTPError as e:
        data = e.read().decode("utf-8")
        print(data, file=sys.stderr)
        raise Exception(f"Request failed with status {e.code}")


def main() -> None:
    """
    Main entry point for the script.
    """
    parser = argparse.ArgumentParser(description="Send data to the /seed endpoint")
    parser.add_argument(
        "--max-batch", type=int, default=100, help="The maximum clusters of records per batch"
    )
    parser.add_argument(
        "--base-url", type=str, default="http://localhost:8080/api", help="The API server URL"
    )

    args = parser.parse_args()

    with sys.stdin as fobj:
        clusters = ijson.items(fobj, "clusters.item", use_float=True)
        batch_iterator = batched_iterator(clusters, args.max_batch)
        for i, batch in enumerate(batch_iterator):
            seed_data(args.base_url, {"clusters": batch})

if __name__ == "__main__":
    main()
