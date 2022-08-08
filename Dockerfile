FROM ubuntu:20.04

# Avoid any UI since we don't have one
ENV DEBIAN_FRONTEND=noninteractive

# Update and install all requirements as well as some useful tools such as net-tools and nano
RUN apt update && apt install -y software-properties-common \
    net-tools nano \
    git \
    clang-11 cmake make \
    libzmq3-dev libssl-dev \
    zlib1g-dev \
    mariadb-server libmariadb-dev \
    python3-pip \
    libluajit-5.1-dev luarocks

ENV DOCKERIZE_VERSION v0.6.1
RUN wget https://github.com/jwilder/dockerize/releases/download/$DOCKERIZE_VERSION/dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && tar -C /usr/local/bin -xzvf dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && rm dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz
    
# Use Clang 11
ENV CC=/usr/bin/clang-11
ENV CXX=/usr/bin/clang++-11

# Python requirements
ADD ./tools/requirements.txt ./tools/requirements.txt
RUN python3 -m pip install -r ./tools/requirements.txt

# Configure and build
ADD . /lsb-src
WORKDIR /lsb-src
RUN mkdir docker_build && cd docker_build && cmake .. && make -j $(nproc)  && cd .. && rm -r docker_build
ADD ./settings/default/ ./settings

ENTRYPOINT [""]