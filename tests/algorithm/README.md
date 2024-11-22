# Record Linkage Algorithm Testing

This repository contains a project to test the effectiveness of the RecordLinker algorithm.

## Prerequisites

Before getting started, ensure you have the following installed:

- [Docker](https://docs.docker.com/engine/install/)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Directory Structure

- `/`: Contains the `.env` file and `Dockerfile` to build
- `configurations/`: Contains the configuration file for the algorithm tests
- `data/`: Contains the data `.csv` files used for the algorithm tests (seed file and test file)
- `results/`: Contains the results of the algorithm tests
- `scripts/`: Contains the scripts to run the algorithm tests

## Steup

1. Build the Docker images:

    ```bash
    docker compose --profile algo-test build
    ```

2. Configure environment variables

    `/algo.env`
    
    Edit the environment variables in the file

3. Edit the algorithm configuration file

    `/configurations/algorithm_configuration.json`

    Edit the configuration file to tune the algorithm parameters

## Running Algorithm Tests

1. Run the test

    Make the script executable
    ```bash
    chmod +x scripts/run_test.py
    ```

    Run the test
    ```bash
    docker compose run --rm algo-test-runner scripts/run_test.py
    ```

2. Analyze the results

    The results of the algorithm tests will be available in the `results/output.csv` file.

    The results will be in a csv formatted file withthe following columns: `Test Case #`, `Expected Result`, `Match Results`, and `Error`.

## Rerunning Algorithm Tests

After you've run the algorithm tests, you may want to rerun the tests with different seed data, test data, or configurations.
Edit the csv files and/or the confirguration file as needed and then run the following commands to rerun the tests.

1. Reset the mpi database
    
    ```bash
    docker compose run --rm algo-test-runner python scripts/reset_db.py
    ```
2. Run the tests
    
    ```bash
    docker compose run --rm algo-test-runner python scripts/run_tests.py
    ```

## Environment Variables

1. `env_file`: The attributes that should be tuned for your particular algorithm test,
    are located in the `algo_test.env` file.

2. `environment`: The attributes that should likely remain static for all algorithm tests are located directly in the `compose.yml` file.

### Algorithm Test Parameters

The following environment variables can be tuned in the `algo-test.env` file:

- `SEED_FILE`: The file containing person data to seed the mpi with
- `TEST_FILE`: The file containing patient data to test the algorithm with
- `ALGORITHM_CONFIGURATION`: The file containing the algorithm configuration json
- `ALGORITHM_NAME`: The name of the algorithm to use (either the name of your `ALGORITHM_CONFIGURATION` or can be the built in `dibbs-basic` or `dibbs-enhanced` algorithms)


## Cleanup

After you've finished running algorithm tests and analyzing the results, you can stop and remove the Docker containers by running:

```bash
docker compose --profile algo-test down
```