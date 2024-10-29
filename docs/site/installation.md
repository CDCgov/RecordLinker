# Installation

This guide provides two installation paths:

1. **Using a pre-built Docker image** from `ghcr.io` for an isolated, containerized setup.
2. **Cloning the source code** and installing dependencies in a Python virtual environment for development and customization.

---

## Option 1: Install with Docker (Recommended for Easy Setup)

### Prerequisites

- Ensure Docker is installed on your system. You can download Docker [here](https://docs.docker.com/get-docker/).

### Steps

1. **Pull the Docker Image**

    Pull the pre-built image from the GitHub Container Registry

    ```bash
    docker pull ghcr.io/cdcgov/recordlinker:latest
    ```
    
1. **Run the Docker Container**
    Launch the container with any necessary environment variables.  Only the `DB_URI` environment variable is required.

    ```bash
    docker run -d -e DB_URI=postgresql+psycopg2://postgres:pw@localhost:5432/postgres -p 8000:8000 ghcr.io/cdcgov/recordlinker:latest
    ```

    > Note: For more information about available environment variables or configuration options, refer to the [Configuration](#configuration) section.

1. **Access the Application**
    The application should now be running in the container. You can access it via your browser at http://localhost:8000.


## Option 2: Install from Source (Recommended for Development)

### Prerequisites

- Python 3.11+ installed on your system.
- Git for cloning the repository.

### Steps

1. **Clone the Repository**
    Clone the repository to your local machine:

    ```bash
    git clone https://github.com/CDCgov/RecordLinker.git
    cd RecordLinker
    ```

1. **Set up a Virtual Environment**
    Create and activate a virtual environment (recommended for isolating dependencies):

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

1. **Install Dependencies**
    Install the necessary dependencies from requirements.txt:

    ```bash
    pip install '.[dev]' # For production dependencies, use `pip install .[prod]`
    ```

1. **Optional: Set Environment Variables**
    Configure environment variables by editing the default .env file in the project root or exporting them directly in your terminal:

    ```bash
    export DB_URI=sqlite:///db.sqlite3
    export CONNECTION_POOL_SIZE=20
    ```

    > Note: For more information about available environment variables or configuration options, refer to the [Configuration](#configuration) section.

1. **Run the Application**
Start the application with the following command:

    ```bash
    uvicorn recordlinker.main:app
    ```

1. **Access the Application**
The application should now be running in the container. You can access it via your browser at http://localhost:8000.
