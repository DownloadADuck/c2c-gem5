# Ubuntu
FROM ubuntu:20.04

# If using apple silicon
#FROM --platform=linux/amd64 ubuntu:20.04

# Environment variable for non-interactive apt installs
ENV DEBIAN_FRONTEND=noninteractive

# Update packages and install dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    scons \
    git \
    vim \
    python3 \
    python3-dev \
    zlib1g \
    zlib1g-dev \
    libprotobuf-dev \
    libprotoc-dev \
    libgoogle-perftools-dev \
    libboost-all-dev \
    libhdf5-serial-dev \
    python3-pydot \
    python3-venv \
    python3-tk \
    pip \
    mypy \
    m4 \
    libcapstone-dev \
    libpng-dev \
    libelf-dev \
    pkg-config \
    wget \
    curl \
    cmake \
    doxygen \
    && rm -rf /var/lib/apt/lists/*

RUN pip install mypy pre-commit

# Set the working directory
WORKDIR /opt/gem5

# Copy the entire repository into the container
COPY . /opt/gem5
