FROM python:3.12-slim

# Set the USE_OTEL environment variable to true to enable OpenTelemetry
ARG USE_OTEL=false
ENV USE_OTEL=${USE_OTEL}

# Updgrade system packages and install curl
RUN apt-get update && apt-get upgrade -y && apt-get install curl -y
RUN pip install --upgrade pip

# Install ODBC driver for SQL Server
RUN apt-get install -y msodbcsql17

WORKDIR /code
# Initialize the recordlinker directory
RUN mkdir -p /code/src/recordlinker

# Copy over just the pyproject.toml file and install the dependencies doing this
# before copying the rest of the code allows for caching of the dependencies
COPY ./pyproject.toml /code/pyproject.toml
RUN pip install '.'

# Conditionally install OpenTelemetry packages if USE_OTEL is true
RUN if [ "$USE_OTEL" = "true" ]; then \
        pip install opentelemetry-distro opentelemetry-exporter-otlp && \
        opentelemetry-bootstrap -a install; \
    fi

# Copy over the rest of the code
COPY ./src /code/src
COPY ./docs /code/docs
COPY ./migrations /code/migrations
COPY ./assets /code/assets
COPY README.md /code/README.md

EXPOSE 8080

# Conditionally run the application with or without OpenTelemetry
CMD if [ "$USE_OTEL" = "true" ]; then \
        opentelemetry-instrument --service_name recordlinker \
            uvicorn recordlinker.main:app --app-dir src --host 0 --port 8080 \
            --log-config src/recordlinker/log_config.yml; \
    else \
        uvicorn recordlinker.main:app --app-dir src --host 0 --port 8080 \
            --log-config src/recordlinker/log_config.yml; \
    fi
