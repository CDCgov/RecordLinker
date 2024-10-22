FROM python:3.12-slim

# Set the USE_OTEL environment variable to true to enable OpenTelemetry
ARG USE_OTEL=false
ENV USE_OTEL=${USE_OTEL}
# Set default log config
ARG LOG_CONFIG=assets/production_log_config.json
ENV LOG_CONFIG=${LOGGING_CONFIG}

# Updgrade system packages and install curl
RUN apt-get update && apt-get upgrade -y && apt-get install curl -y
RUN pip install --upgrade pip

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
COPY ./migrations /code/migrations
COPY ./assets /code/assets
COPY README.md /code/README.md

EXPOSE 8080

# Conditionally run the application with or without OpenTelemetry
CMD if [ "$USE_OTEL" = "true" ]; then \
        opentelemetry-instrument --service_name recordlinker \
            uvicorn recordlinker.main:app --host 0 --port 8080; \
    else \
        uvicorn recordlinker.main:app --host 0 --port 8080; \
    fi
