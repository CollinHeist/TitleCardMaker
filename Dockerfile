# Create pipenv image to convert Pipfile to requirements.txt
FROM python:3.9-slim as pipenv

# Copy Pipfile and Pipfile.lock
COPY Pipfile Pipfile.lock ./

# Install pipenv and convert to requirements.txt
RUN pip3 install --no-cache-dir --upgrade pipenv; \
    pipenv requirements > requirements.txt

FROM python:3.9-slim as python-reqs

# Copy requirements.txt from pipenv stage
COPY --from=pipenv /requirements.txt requirements.txt

# Install gcc for building python dependencies; install TCM dependencies
RUN apt-get update; \
    apt-get install -y gcc; \
    pip3 install --no-cache-dir -r requirements.txt

# Set base image for running TCM
FROM python:3.9-slim
LABEL maintainer="CollinHeist" \
      description="Automated title card maker for Plex"

# Set working directory, copy source into container
WORKDIR /maker
COPY . /maker

# Copy python packages from python-reqs
COPY --from=python-reqs /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages

# Script environment variables
ENV TCM_PREFERENCES=/config/preferences.yml \
    TCM_IS_DOCKER=TRUE

# Delete setup files
# Create user and group to run the container
# Install gosu, imagemagick
# Clean up apt cache
# Override default ImageMagick policy XML file
RUN set -eux; \
    rm -f Pipfile Pipfile.lock; \
    groupadd -g 314 titlecardmaker; \
    useradd -u 314 -g 314 titlecardmaker; \
    apt-get update; \
    apt-get install -y librsvg2-bin; \
    apt-get install -y --no-install-recommends gosu imagemagick; \
    rm -rf /var/lib/apt/lists/*; \
    cp modules/ref/policy.xml /etc/ImageMagick-6/policy.xml

# Entrypoint
CMD ["python3", "main.py", "--run", "--no-color"]
ENTRYPOINT ["bash", "./start.sh"]