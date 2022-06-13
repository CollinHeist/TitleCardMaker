# syntax=docker/dockerfile:1

# Set base image
FROM python:3.9-slim
LABEL maintainer="CollinHeist"
LABEL description="Automated title card maker for Plex"

# Set working directory, copy source into container
WORKDIR /maker
COPY . /maker

# Script environments
ENV TCM_PREFERENCES=/config/preferences.yml

# Create user and group to run the container
RUN groupadd -g 314 titlecardmaker; \
    useradd -u 314 -g 314 titlecardmaker

# Install gosu
RUN set -eux; \
    apt-get update; \
    apt-get install -y gosu; \
    rm -rf /var/lib/apt/lists/*; \
    gosu nobody true

# Intall OS dependencies
RUN apt-get update; \
    apt-get upgrade -y; \
    apt update

# Install ImageMagick
RUN apt install -y imagemagick
RUN export MAGICK_HOME="$HOME/ImageMagick-7.1.0"; \
    export PATH="$MAGICK_HOME/bin:$PATH"; \
    export DYLD_LIBRARY_PATH="$MAGICK_HOME/lib/"

# Install TCM package dependencies
RUN pip3 install --no-cache-dir --upgrade pipenv; \
    pipenv lock --keep-outdated --requirements > requirements.txt; \
    pip3 install -r requirements.txt

# Delete setup files
RUN rm -f Pipfile Pipfile.lock requirements.txt 

# Entrypoint
CMD ["python3", "main.py", "--run", "--no-color"]
ENTRYPOINT ["bash", "./start.sh"]
