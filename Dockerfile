# syntax=docker/dockerfile:1
# Create pipenv image to convert Pipfile to requirements.txt
FROM python:3.11-slim as pipenv

# Copy Pipfile and Pipfile.lock
COPY Pipfile Pipfile.lock ./

# Install pipenv and convert to requirements.txt
RUN pip3 install --no-cache-dir --upgrade pipenv; \
    pipenv requirements > requirements.txt

FROM python:3.11-slim as python-reqs

# Copy requirements.txt from pipenv stage
COPY --from=pipenv /requirements.txt requirements.txt

# Install gcc for building python dependencies; install TCM dependencies
RUN apt-get update && \
    apt-get install -y gcc && \
    pip3 install --no-cache-dir -r requirements.txt

# Set base image for running TCM
FROM python:3.11-slim
LABEL maintainer="CollinHeist" \
      description="Automated Title card maker for Emby, Jellyfin, and Plex" \
      version="v2.0-alpha.5.2"

# Set working directory, copy source into container
WORKDIR /maker
COPY . /maker

# Copy python packages from python-reqs
COPY --from=python-reqs /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Script environment variables
ENV TCM_PREFERENCES=/config/preferences.yml \
    TCM_IS_DOCKER=TRUE \
    TZ=UTC

# Finalize setup
RUN \
    # Create user and group to run TCM
    set -eux && \
    rm -f Pipfile Pipfile.lock && \
    groupadd -g 100 titlecardmaker && \
    useradd -u 99 -g 100 titlecardmaker && \
    # Install imagemagick and curl (for healthcheck)
    apt-get update && \
    apt-get install -y --no-install-recommends curl imagemagick libmagickcore-6.q16-6-extra && \
    cp modules/ref/policy.xml /etc/ImageMagick-6/policy.xml && \
    # Remove apt cache and setup files
    rm -rf /tmp/* /var/tmp/* /var/lib/apt/lists/*

# Expose TCM Port
EXPOSE 4242

# Healthcheck command
# Add --start-interval=10s back in when merged in Docker v24/v25
HEALTHCHECK --interval=3m --timeout=10s --start-period=3m \
    CMD curl --fail http://0.0.0.0:4242/api/healthcheck || exit 1

# Entrypoint
CMD ["python3", "-m", "uvicorn", "app-main:app", "--host", "0.0.0.0", "--port", "4242"]
ENTRYPOINT ["bash", "./start.sh"]
