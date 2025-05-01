FROM python:3.12-slim

LABEL org.opencontainers.image.source=https://github.com/CDCgov/RecordLinker
LABEL org.opencontainers.image.description="RecordLinker is a service that links records from two datasets based on a set of common attributes."
LABEL org.opencontainers.image.licenses=Apache-2.0

# Set the environment variable to prod by default
ARG ENVIRONMENT=prod
ENV ENVIRONMENT=${ENVIRONMENT}
# Set the port variable to 8080 by default
ARG PORT=8080
ENV PORT=${PORT}
# Set the USE_MSSQL env variable to true to enable SQL Server support
ARG USE_MSSQL=true
ENV USE_MSSQL=${USE_MSSQL}
# Set the USE_OTEL env variable to true to enable OpenTelemetry
ARG USE_OTEL=false
ENV USE_OTEL=${USE_OTEL}
# Set default log config
ARG LOG_CONFIG=assets/production_log_config.json
ENV LOG_CONFIG=${LOG_CONFIG}

# Updgrade system packages
RUN apt-get update && apt-get upgrade -y
RUN pip install --upgrade pip

# Avoid interactive prompts and upgrade linux-libc-dev and curl
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    linux-libc-dev curl && \
    rm -rf /var/lib/apt/lists/*

# Conditionally install ODBC driver for SQL Server.
RUN if [ "$USE_MSSQL" = "true" ]; then \
        apt-get install -y gnupg2 apt-transport-https && \
        curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /etc/apt/trusted.gpg.d/microsoft.gpg && \
        curl https://packages.microsoft.com/config/debian/11/prod.list | tee /etc/apt/sources.list.d/mssql-release.list && \
        apt-get update && \
        ACCEPT_EULA=Y apt-get install -y msodbcsql18 unixodbc-dev; \
    fi

WORKDIR /code
# Initialize the recordlinker directory
RUN mkdir -p /code/src/recordlinker

# Copy over just the pyproject.toml file and install the dependencies doing this
# before copying the rest of the code allows for caching of the dependencies
COPY ./pyproject.toml /code/pyproject.toml
RUN pip install "$(printf '%s' ".[${ENVIRONMENT}]")"

# Conditionally install OpenTelemetry packages if USE_OTEL is true
RUN if [ "$USE_OTEL" = "true" ]; then \
        pip install opentelemetry-distro opentelemetry-exporter-otlp && \
        opentelemetry-bootstrap -a install; \
    fi

# Copy over the rest of the code
COPY ./src /code/src
COPY ./docs /code/docs
COPY README.md /code/README.md

EXPOSE ${PORT}

# Create an entrypoint script
RUN echo '#!/bin/sh' > /entrypoint.sh && \
    echo 'exec uvicorn recordlinker.main:app --app-dir src --host 0 --port "$PORT"' >> /entrypoint.sh && \
    chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
