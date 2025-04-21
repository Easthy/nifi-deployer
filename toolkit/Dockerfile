FROM python:3.7-slim-buster

ENV NIFI_VERSION 1.16.1

USER root
RUN useradd -ms /bin/bash nifi

# Create folder required for java installation
RUN mkdir -p /usr/share/man/man1 /usr/share/man/man2

# Installing JAVA 11 & other tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    openjdk-11-jre \
    wget telnet curl nano unzip

RUN mkdir -p /opt/nifi && \
    mkdir -p /opt/certs
RUN chown -R nifi: /opt/nifi && \
    chown -R nifi: /opt/certs

USER nifi
# Download NiFi Toolkit
RUN cd /opt/nifi && \
    wget https://downloads.apache.org/nifi/${NIFI_VERSION}/nifi-toolkit-${NIFI_VERSION}-bin.zip && \
    unzip nifi-toolkit-${NIFI_VERSION}-bin.zip && \
    mv nifi-toolkit-${NIFI_VERSION} toolkit && \
    rm nifi-toolkit-${NIFI_VERSION}-bin.zip

# Create certificate for admin user
RUN cd /opt/nifi/toolkit && ls && \
    ./bin/tls-toolkit.sh standalone -n "localhost" --subjectAlternativeNames "nifi, nifi-registry" -C "CN=admin, OU=NIFI" -o "auth-certs-san"

ENV TOOLKIT_CERTIFICATE_FOLDER /opt/nifi/toolkit/auth-certs-san/localhost

RUN cp $TOOLKIT_CERTIFICATE_FOLDER/keystore.jks /opt/certs/keystore.jks && \
    cp $TOOLKIT_CERTIFICATE_FOLDER/truststore.jks /opt/certs/truststore.jks

# Set nifi.properties
ENV INITIAL_ADMIN_IDENTITY 'CN=admin, OU=NIFI'
ENV INITIAL_USER_IDENTITY 'CN=admin, OU=NIFI'

ENV KEYSTORE_TYPE JKS
ENV TRUSTSTORE_TYPE JKS
ENV KEYSTORE_PATH /opt/certs/keystore.jks
ENV TRUSTSTORE_PATH /opt/certs/truststore.jks

