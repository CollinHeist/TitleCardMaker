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

# Delete setup files
# Create user and group to run the container
# Clean up apt cache
RUN set -eux && \
    rm -f Pipfile Pipfile.lock && \
    groupadd -g 314 titlecardmaker && \
    useradd -u 314 -g 314 titlecardmaker && \
    apt-get update && \
    apt-get install -y --no-install-recommends imagemagick libmagickcore-6.q16-6-extra && \
    rm -rf /var/lib/apt/lists/* && \
    cp modules/ref/policy.xml /etc/ImageMagick-6/policy.xml

# Expose TCM Port
EXPOSE 4242

# Healthcheck command
HEALTHCHECK --interval=5m --timeout=20s --start-period=3m --start-interval=10s \
    CMD curl --fail http://localhost:4242/ || exit 1

# Entrypoint
CMD ["python3", "-m", "uvicorn", "app-main:app", "--host", "0.0.0.0", "--port", "4242"]
ENTRYPOINT ["bash", "./start.sh"]