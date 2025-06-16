# Record Linker – Locust Load Testing

This project includes a [Locust-based](https://locust.io/) load test suite for testing
performance of the Record Linker API.

## Setup

### 1. Set up development environment. 

Go through the development setup instructions in the [README](../README.md), this will install the necessary dependencies and set up a Python virtual environment.
```sh
source scripts/bootstrap.sh
```

### 2. Generate `record-data` file with sample records to send to the Record Linker API.

The load tests requires 1 data file to simulate the test.  This file, called `record-data`, will contain  sample records in it, 
    that the testing framework will use to send requests to the Record Linker API.
This is called the `record-data` file.  You can use the [generate test data script](../scripts/gen_seed_test_data.py) to generate a sample file.  See that script for more details on how to create a test data file.
```sh
python scripts/gen_seed_test_data.py --count 100 > record-data.json
```

### 3. [OPTIONAL] Generate the `seed-data` file, which can be used to seed the database with records before the test starts.

This is optional, as it's fine to start the test from an empty database.  Again, you can use the same [generate test data script](../scripts/gen_seed_test_data.py) to generate a test seed data file.
```sh
python scripts/gen_seed_test_data.py --count 9999 > seed-data.json
```

### 4. [OPTIONAL] Scramble the `record-data` file.

A scrambling script has been included to randomize the data in the `record-data` file. See
[scramble data script](scripts/scramble_data.py) for more details.

### 5. Run an instance of the Record Linker API.

The locust test suite will need an instance of the Record Linker API running.  This could be a local instance, or possibly over the network.  For a simple test, you can use the [local server script](../scripts/local_server.sh). See the [README](../README.md) for more details on a local setup and how to run the local server.
```sh
./scripts/local_server.sh
```

## Running the Locust Test Suite

To run the Locust test for 10 seconds with a load of 2 users and 100 records to link, use the following command:

```bash
locust -f locustfile.py \
    --headless \
    -u 2 -r 2 \
    --run-time 10s \
    --records-to-link 100 \
    --record-data assets/test_data.json
```

### Custom Parameters

| Argument             | Type     | Default                 | Description                                         |
|----------------------|----------|-------------------------|-----------------------------------------------------|
| `--records-to-link`  | `int`    | `0`                     | Number of records to link in the test run, 0 for infinite. |
| `--link-probability` | `float`  | `0.5`                   | Probability that any given record will be linked.  |
| `--seed-data`        | `str`    | ` `                     | Path to the seed data file.                        |
| `--record-data`      | `str`    | `assets/test_data.json` | Path to the record data file.                      |
| `--linkage-endpoint` | `choice` | `match`                 | Which linkage endpoint to test, `match` or `link`  |

### UI mode

You can run the tests, and control the parameters, in the browser by removing the `--headless` flag.
Visit http://localhost:8089 to view the UI.

```sh
locust -f locustfile.py
```

### 📍 Notes

See `locust --help` for information on more options.
