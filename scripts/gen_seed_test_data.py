#!/usr/bin/env python
"""
scripts/gen_seed_test_data.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Script to generate test data for the /seed endpoint in the RecordLinker project.

The script will emit a JSON object to STDOUT containing a list of clusters, each with a
list of PII records. By default, 100 clusters will be generated, each with a random number
of PII records up to 25. Those values can be adjusted see --help for more information.
"""

import argparse
import datetime
import random
import string
import sys
import typing

import pydantic
from faker import Faker

from recordlinker import schemas
from recordlinker.schemas.identifier import Identifier
from recordlinker.schemas.identifier import IdentifierType
from recordlinker.schemas.pii import Address
from recordlinker.schemas.pii import Name
from recordlinker.schemas.pii import Race
from recordlinker.schemas.pii import Sex
from recordlinker.schemas.pii import Telecom


def _generate_random_identifiers(count, faker):
    """
    Given a count of identifiers to generate, generate a list of
    MRNs, SSNs, and Drivers Licenses.
    """
    for idx in range(count):
        if idx % 3 == 0:
            # make mrn
            yield Identifier(type=IdentifierType.MR, value=faker.bothify(text="MRN-#######"))
        if idx % 3 == 1:
            # make ssn
            yield Identifier(type=IdentifierType.SS, value=faker.ssn())
        if idx % 3 == 2:
            # make drivers_license
            yield Identifier(
                type=IdentifierType.DL, value=faker.bothify(text="DL-######"), authority=faker.state_abbr()
            )


# Function to generate random data
def _generate_random_pii_record(faker):
    return schemas.PIIRecord(
        external_id=faker.uuid4(),
        birth_date=faker.date_of_birth(minimum_age=0, maximum_age=100),
        sex=random.choice(list(Sex)),
        address=[
            Address(
                line=[faker.street_address()],
                city=faker.city(),
                state=faker.state_abbr(),
                postal_code=faker.zipcode(),
                county=faker.city(),
                country=faker.country_code(),
                latitude=faker.latitude(),
                longitude=faker.longitude(),
            )
        ],
        name=[
            Name(
                family=faker.last_name(),
                given=[faker.first_name()],
                use=random.choice(["official", "usual", "nickname"]),
            )
        ],
        telecom=[
            Telecom(
                value=faker.phone_number(),
                system="phone",
                use=random.choice(["home", "work", "mobile"]),
            )
        ],
        race=[str(random.choice(list(Race)))],
        identifiers=list(_generate_random_identifiers(random.randint(1, 3), faker)),
    )


def _transform(val: typing.Any, str_edits: tuple[int, int] = (1, 3)) -> typing.Any:
    if val:
        if isinstance(val, datetime.date):
            action = random.choice(["year", "month", "day"])
            if action == "month":
                adjustment = random.randint(1, 12) * 30
            elif action == "day":
                adjustment = random.randint(0, 30)
            elif action == "year":
                # Randomly adjust the year by up to 10 years
                adjustment = random.randint(0, 10) * 365
            return val - datetime.timedelta(days=adjustment)
        elif isinstance(val, str):
            chars = list(val)
            for _ in range(random.randint(str_edits[0], str_edits[1])):
                action = random.choice(["add", "delete", "transpose"])
                if action == "add":
                    idx = random.randint(0, len(chars))
                    chars.insert(idx, random.choice(string.ascii_letters))
                elif action == "delete" and chars:
                    idx = random.randint(0, len(chars) - 1)
                    del chars[idx]
                elif action == "transpose" and len(chars) > 1:
                    idx = random.randint(0, len(chars) - 2)
                    chars[idx], chars[idx + 1] = chars[idx + 1], chars[idx]
            return "".join(chars)
    return val


def _scramble(
    record: schemas.PIIRecord,
    scamble_frequency: float = 0.1,
    str_edits: tuple[int, int] = (1, 3),
    drop_frequency: float = 0.1,
    transformer: typing.Callable[[typing.Any, tuple[int, int]], typing.Any] = _transform,
) -> schemas.PIIRecord:
    """
    Scrambles a subset of relevant fields and returns the scrambled dict.
    """

    def _walk(val):
        if isinstance(val, pydantic.BaseModel):
            for field_name, value in val:
                setattr(val, field_name, _walk(value))
        elif isinstance(val, list):
            for i, item in enumerate(val):
                val[i] = _walk(item)
        elif isinstance(val, dict):
            for key, value in val.items():
                val[key] = _walk(value)
        else:
            if random.random() < scamble_frequency:
                return transformer(val, str_edits)
            elif random.random() < drop_frequency:
                if isinstance(val, str):
                    return ""
        return val

    return _walk(record.model_copy(deep=True))


def main() -> None:
    """
    Main entry point for the script.
    """
    parser = argparse.ArgumentParser(description="Generate test data for the /seed endpoint")
    parser.add_argument(
        "--count",
        type=int,
        default=100,
        help="The number of clusters to generate",
    )
    parser.add_argument(
        "--max-per-cluster",
        type=int,
        default=25,
        help="The maximum number of records per cluster",
    )
    parser.add_argument(
        "--scramble-freq",
        type=float,
        default=0.1,
        help="The frequency of scrambling record fields",
    )
    parser.add_argument(
        "--drop-freq",
        type=float,
        default=0.1,
        help="The frequency of dropping record fields",
    )
    parser.add_argument(
        "--str-edits",
        type=int,
        nargs=2,
        default=(1, 3),
        help="The minimum and maximum number of string edits to apply",
    )

    args = parser.parse_args()

    faker = Faker()
    sys.stdout.write('{\n"clusters": [\n')
    first = True
    for _ in range(args.count):
        records: list[schemas.PIIRecord] = [_generate_random_pii_record(faker)]
        for _ in range(random.randint(1, args.max_per_cluster)):
            records.append(
                _scramble(
                    records[0],
                    scamble_frequency=args.scramble_freq,
                    drop_frequency=args.drop_freq,
                    str_edits=args.str_edits,
                )
            )
        cluster = schemas.Cluster(
            external_person_id=f"EP:{str(faker.uuid4())}",
            records=records,
        )
        if not first:
            sys.stdout.write(",\n")
        sys.stdout.write(f"{cluster.model_dump_json(indent=2)}")
        first = False
    sys.stdout.write("\n]}\n")


if __name__ == "__main__":
    main()
