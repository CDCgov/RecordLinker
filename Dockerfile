FROM python:3.12-slim

# Set the USE_OTEL env variable to true to enable OpenTelemetry
ARG USE_OTEL=false
ENV USE_OTEL=${USE_OTEL}
# Set the USE_MSSQL env variable to true to enable SQL Server support
ARG USE_MSSQL=true
ENV USE_MSSQL=${USE_MSSQL}
# Set default log config
ARG LOG_CONFIG=/code/assets/production_log_config.json
ENV LOG_CONFIG=${LOGGING_CONFIG}

# Updgrade system packages and install curl
RUN apt-get update && apt-get upgrade -y && apt-get install curl -y
RUN pip install --upgrade pip

# Conditionally install ODBC driver for SQL Server
RUN if [ "$USE_MSSQL" = "true" ]; then \
        apt-get install -y gnupg2 apt-transport-https && \
        curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /etc/apt/trusted.gpg.d/microsoft.gpg && \
        curl https://packages.microsoft.com/config/debian/11/prod.list | tee /etc/apt/sources.list.d/mssql-release.list && \
        apt-get update && \
        ACCEPT_EULA=Y apt-get install -y msodbcsql17 unixodbc-dev; \
    fi

WORKDIR /code
# Initialize the recordlinker directory
RUN mkdir -p /code/src/recordlinker

# Copy over just the pyproject.toml file and install the dependencies doing this
# before copying the rest of the code allows for caching of the dependencies
COPY ./pyproject.toml /code/pyproject.toml
RUN pip install '.[prod]'

# Conditionally install OpenTelemetry packages if USE_OTEL is true
RUN if [ "$USE_OTEL" = "true" ]; then \
        pip install opentelemetry-distro opentelemetry-exporter-otlp && \
        opentelemetry-bootstrap -a install; \
    fi

# Copy over the rest of the code
COPY ./src /code/src
COPY ./docs /code/docs
COPY ./assets /code/assets
COPY README.md /code/README.md

EXPOSE 8080

# Conditionally run the application with or without OpenTelemetry
CMD if [ "$USE_OTEL" = "true" ]; then \
        opentelemetry-instrument --service_name recordlinker \
            uvicorn recordlinker.main:app --app-dir src --host 0 --port 8080; \
    else \
        uvicorn recordlinker.main:app --app-dir src --host 0 --port 8080; \
    fi
