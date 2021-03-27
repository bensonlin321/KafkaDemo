FROM ubuntu:18.04
ENV DEBIAN_FRONTEND noninteractive
MAINTAINER BensonLin

RUN echo "#!/bin/sh\nexit 0" > /usr/sbin/policy-rc.d
ENV KAFKA_HEAP_OPTS="-Xmx256M -Xms128M"
ENV JAVA_HOME=/usr/lib/jdk1.8.0_211
ENV PATH=$PATH:$JAVA_HOME/bin

# setup
RUN apt-get update
RUN apt-get install -y g++ software-properties-common build-essential language-pack-en unzip curl wget vim libpam0g-dev libssl-dev cmake cron
RUN apt-get install -y iputils-ping
RUN add-apt-repository ppa:deadsnakes/ppa -y
RUN apt install -y python3-pip

# copy file to temp
COPY ./ /temp

# install kafka, nginx, php
WORKDIR /temp/install
RUN ./install.sh

WORKDIR /temp
ENTRYPOINT /temp/install/launch_nginx.sh && /temp/install/launch_kafka.sh && /temp/install/launch_consumer.sh && /bin/bash
