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

# Updgrade system packages and install curl
RUN apt-get update && apt-get upgrade -y && apt-get install curl -y
RUN pip install --upgrade pip

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
RUN mkdir -p /code/apps/recordlinker

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
COPY ./apps/recordlinker /code/apps/recordlinker
COPY ./docs /code/docs
COPY README.md /code/README.md

EXPOSE ${PORT}

# Web application - Record Linker user interface

# Set the port variable to 3000 by default
ARG WEBAPP_PORT=3000
ENV WEBAPP_PORT=${WEBAPP_PORT}

# Install Node.js and npm
RUN apt-get update && apt-get install -y nodejs npm

# Verify installations
RUN node -v && npm -v

# Install dependencies for webapp
RUN mkdir -p /code/webapp
COPY ./apps/webapp /code/webapp
WORKDIR /code/webapp
RUN npm install --legacy-peer-deps

#NEXT_TELEMETRY_DISABLED=1

# Build and deploy webapp
RUN npm run build

# copy to the static file folder

WORKDIR /code

# Create an entrypoint script
RUN echo '#!/bin/sh' > /entrypoint.sh && \
    echo 'PORT=$WEBAPP_PORT nohup node webapp/.next/standalone/server.js &' >> /entrypoint.sh && \
    echo 'PORT=$PORT' >> /entrypoint.sh && \
    echo 'exec uvicorn recordlinker.main:app --app-dir apps --host 0 --port "$PORT"' >> /entrypoint.sh && \
    echo 'wait -n' >> /entrypoint.sh && \
    echo 'exit \$?' >> /entrypoint.sh && \
    chmod +x /entrypoint.sh

# add the  command to start the web application here 
ENTRYPOINT ["/entrypoint.sh"]
