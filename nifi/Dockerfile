FROM local-toolkit

ENV NIFI_HOME /opt/nifi/nifi-current

USER nifi

# Download package
RUN mkdir -p /opt/nifi && \
    cd /opt/nifi && \
    wget https://dlcdn.apache.org/nifi/${NIFI_VERSION}/nifi-${NIFI_VERSION}-bin.zip && \
    unzip nifi-${NIFI_VERSION}-bin.zip && \
    mv nifi-${NIFI_VERSION} nifi-current && \
    rm nifi-${NIFI_VERSION}-bin.zip

RUN mkdir -p /opt/nifi/nifi-current/scripts

USER nifi

COPY scripts /opt/nifi/scripts

USER root
RUN chmod -R +x /opt/nifi/scripts
RUN chown -R nifi: ${NIFI_HOME}

USER nifi
WORKDIR ${NIFI_HOME}

ENTRYPOINT ["/opt/nifi/scripts/start-nifi.sh"]