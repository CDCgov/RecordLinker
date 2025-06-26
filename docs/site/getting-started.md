# Getting Started

## Installation

### Option 1: Quick Start with Docker (Recommended)

#### Prerequisites

- Make sure [Docker is installed](https://docs.docker.com/get-docker/) on your machine.

#### Steps

1. **Start the docker container**
   Run the container with a mounted volume to persist the SQLite database on your host. The only required environment variable is `DB_URI`:
```bash
docker run -v ./:/tmp -e DB_URI=sqlite:////tmp/db.sqlite3 ghcr.io/cdcgov/recordlinker:latest
```
> 💡 For a full list of configuration options, see the [Application Configuration](app-configuration.md) page.

2. **Access the application**
   Once the container is running, the app will be available at [http://localhost:8080](http://localhost:8080).

### Option 2: Install from Source (Recommended for Development)

#### Prerequisites

- Python 3.11+ installed on your system.
- Git for cloning the repository.

#### Steps

1. **Clone the repository**
    Clone the repository to your local machine:

    ```
    git clone https://github.com/CDCgov/RecordLinker.git
    cd RecordLinker
    ```

1. **Bootstrap a virtual environment**
    Create and activate a virtual environment (recommended for isolating dependencies):

    ```
    source ./scripts/bootstrap.sh
    ```

1. **Start the application**
Start the application with the following command:

    ```
    ./scripts/local_server.sh
    ```

1. **Access the application**
The application should now be running in the container. You can access it via your browser at [http://localhost:8080](http://localhost:8080).

## Example usage

We've included a script in the repository that configures an algorithm, seeds sample data, and runs
a linkage test. Running this script is a quick way to explore how to interact with the application
API. It assumes you have the application running locally—either via Docker or the local server
script—and requires both `curl` and `python3` to be installed. We recommend reviewing the script
itself to better understand the steps involved and adapt them to your needs.

```bash
bash <(curl -sSL https://raw.githubusercontent.com/CDCgov/RecordLinker/main/scripts/example_linkage_test.sh)
```
