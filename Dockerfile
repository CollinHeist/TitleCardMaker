# syntax=docker/dockerfile:1
FROM python:3.11-slim AS python-reqs
# run static install
# Install gcc for building python dependencies
RUN apt-get update && \
    apt-get install -y gcc
RUN pip3 install --no-cache-dir --upgrade pipenv

# Install pipenv and convert to requirements.txt
COPY Pipfile Pipfile.lock ./
RUN pipenv requirements > requirements.txt

# install TCM dependencies
RUN --mount=type=cache,target=/root/.cache \
    pip3 install -r requirements.txt

# Set base image for running TCM
FROM python:3.11-slim AS final
LABEL maintainer="CollinHeist" \
      description="Automated Title card maker for Emby, Jellyfin, and Plex" \
      version="v2.0-alpha.10.0"
# Script environment variables
ENV TCM_IS_DOCKER=TRUE \
    TZ=UTC

# Install static dependencies
RUN \
    # Create user and group to run TCM
    set -eux && \
    groupadd -g 314 titlecardmaker && \
    useradd -u 314 -g 314 titlecardmaker
# Install imagemagick and curl (for healthcheck)
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl imagemagick libmagickcore-6.q16-6-extra && \
    # Remove apt cache and setup files
    rm -rf /tmp/* /var/tmp/* /var/lib/apt/lists/*

# Copy python packages from python-reqs
COPY --from=python-reqs /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Set working directory, copy source into container
WORKDIR /maker
COPY . /maker

# Finalize setup
RUN cp modules/ref/policy.xml /etc/ImageMagick-6/policy.xml && \
    rm -f Pipfile Pipfile.lock
# Expose TCM Port
EXPOSE 4242

# Healthcheck command
# Add --start-interval=10s back in when merged in Docker v24/v25
HEALTHCHECK --interval=3m --timeout=10s --start-period=3m \
    CMD curl --fail http://0.0.0.0:4242/api/healthcheck || exit 1

# Entrypoint
CMD ["python3", "-u", "-m", "uvicorn", "app-main:app", "--host", "0.0.0.0", "--port", "4242"]
ENTRYPOINT ["bash", "./start.sh"]