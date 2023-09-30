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
      description="Automated Title card maker for Emby, Jellyfin, and Plex"
      version="v2.0-alpha.5.2"

# Set working directory, copy source into container
WORKDIR /maker
COPY . /maker

# Copy python packages from python-reqs
COPY --from=python-reqs /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Script environment variables
ENV TCM_PREFERENCES=/config/preferences.yml \
    TCM_IS_DOCKER=TRUE

# These are from the dpokidov/imagemagick Docker container
# https://hub.docker.com/r/dpokidov/imagemagick/dockerfile
ARG IM_VERSION=7.1.1-8
ARG LIB_HEIF_VERSION=1.12.0
ARG LIB_AOM_VERSION=3.1.0
ARG LIB_WEBP_VERSION=1.2.0

RUN apt-get -y update && \
    apt-get -y upgrade && \
    apt-get install -y git make gcc pkg-config autoconf curl g++ \
    # libaom
    yasm cmake \
    # libheif
    libde265-0 libde265-dev libjpeg62-turbo libjpeg62-turbo-dev x265 libx265-dev libtool \
    # IM
    libpng16-16 libpng-dev libjpeg62-turbo libjpeg62-turbo-dev libgomp1 ghostscript libxml2-dev libxml2-utils libtiff-dev libfontconfig1-dev libfreetype6-dev && \
    # Building libwebp
    cd / && \
    git clone https://chromium.googlesource.com/webm/libwebp && \
    cd libwebp && git checkout v${LIB_WEBP_VERSION} && \
    ./autogen.sh && ./configure --enable-shared --enable-libwebpdecoder --enable-libwebpdemux --enable-libwebpmux --enable-static=no && \
    make && make install && \
    ldconfig /usr/local/lib && \
    cd ../ && rm -rf libwebp && \
    # Building libaom
    git clone https://aomedia.googlesource.com/aom && \
    cd aom && git checkout v${LIB_AOM_VERSION} && cd .. && \
    mkdir build_aom && \
    cd build_aom && \
    cmake ../aom/ -DENABLE_TESTS=0 -DBUILD_SHARED_LIBS=1 && make && make install && \
    ldconfig /usr/local/lib && \
    cd .. && \
    rm -rf aom && \
    rm -rf build_aom && \
    # Building libheif
    curl -L https://github.com/strukturag/libheif/releases/download/v${LIB_HEIF_VERSION}/libheif-${LIB_HEIF_VERSION}.tar.gz -o libheif.tar.gz && \
    tar -xzvf libheif.tar.gz && cd libheif-${LIB_HEIF_VERSION}/ && ./autogen.sh && ./configure && make && make install && cd .. && \
    ldconfig /usr/local/lib && \
    rm -rf libheif-${LIB_HEIF_VERSION} && rm libheif.tar.gz && \
    # Building ImageMagick
    git clone https://github.com/ImageMagick/ImageMagick.git && \
    cd ImageMagick && git checkout ${IM_VERSION} && \
    ./configure --without-magick-plus-plus --disable-docs --disable-static --with-libtiff && \
    make && make install && \
    ldconfig /usr/local/lib && \
    apt-get remove --autoremove --purge -y gcc make cmake curl g++ yasm git autoconf pkg-config libpng-dev libjpeg62-turbo-dev libde265-dev libx265-dev libxml2-dev libtiff-dev libfontconfig1-dev libfreetype6-dev && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf ImageMagick && \
    # Override default ImageMagick policy
    cp /maker/modules/ref/policy.xml /usr/local/etc/ImageMagick-7/policy.xml

# Delete setup files
# Create user and group to run the container
# Clean up apt cache
RUN set -eux && \
    rm -f Pipfile Pipfile.lock && \
    groupadd -g 314 titlecardmaker && \
    useradd -u 314 -g 314 titlecardmaker

# Expose TCM Port
EXPOSE 4242

# Entrypoint
CMD ["python3", "-m", "uvicorn", "app-main:app", "--host", "0.0.0.0", "--port", "4242"]
ENTRYPOINT ["bash", "./start.sh"]