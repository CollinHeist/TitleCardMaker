# syntax=docker/dockerfile:1

# Set base image
FROM python:3.9-slim

# Set working directory
WORKDIR /maker

# Copy source content into container
COPY . /maker

# Intall OS dependencies
RUN echo "System Setup"
RUN apt-get update
RUN apt-get upgrade -y
RUN apt update

# Install ImageMagick
RUN apt install -y imagemagick
RUN export MAGICK_HOME="$HOME/ImageMagick-7.1.0" \
  && export PATH="$MAGICK_HOME/bin:$PATH" \
  && export DYLD_LIBRARY_PATH="$MAGICK_HOME/lib/"

# Install TCM package dependencies
RUN pip3 install --no-cache-dir --upgrade pipenv
RUN pipenv install

# Entrypoint
ENTRYPOINT ["/bin/bash"]