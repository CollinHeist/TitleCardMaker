# Create pipenv image to convert Pipfile to requirements.txt
FROM python:3.9-slim as pipenv

# Copy Pipfile and Pipfile.lock
COPY Pipfile Pipfile.lock ./

# Install pipenv and convert to requirements.txt
RUN pip3 install --no-cache-dir --upgrade pipenv; \
    pipenv requirements > requirements.txt

FROM python:3.9-slim as builder

# Install gcc for building python dependencies
RUN apt-get update; \
    apt-get install -y gcc

# Copy requirements.txt from pipenv stage
COPY --from=pipenv /requirements.txt requirements.txt

# Install TCM package dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Set base image for running TCM
FROM python:3.9-slim
LABEL maintainer="CollinHeist"
LABEL description="Automated title card maker for Plex"

# Set working directory, copy source into container
WORKDIR /maker
COPY . /maker

# Delete setup files
RUN rm -f Pipfile Pipfile.lock

# Copy python packages from builderCOPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages

# Script environment variables
ENV TCM_PREFERENCES=/config/preferences.yml \
    TCM_IS_DOCKER=TRUE

# Create user and group to run the container
RUN groupadd -g 314 titlecardmaker; \
    useradd -u 314 -g 314 titlecardmaker

# Install gosu and imagemagick; clean up apt cache
RUN set -eux; \
    apt-get update; \
    apt-get install -y gosu imagemagick; \
    rm -rf /var/lib/apt/lists/*


# Override default ImageMagick policy XML file
COPY modules/ref/policy.xml /etc/ImageMagick-6/policy.xml

# Entrypoint
CMD ["python3", "main.py", "--run", "--no-color"]
ENTRYPOINT ["bash", "./start.sh"]