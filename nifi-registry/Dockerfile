FROM local-toolkit

ENV NIFI_REGISTRY_HOME /opt/nifi/nifi-registry-current

USER nifi

# Download package
RUN mkdir -p /opt/nifi && \
    cd /opt/nifi && \
    wget https://dlcdn.apache.org/nifi/${NIFI_VERSION}/nifi-registry-${NIFI_VERSION}-bin.zip && \
    unzip nifi-registry-${NIFI_VERSION}-bin.zip && \
    mv nifi-registry-${NIFI_VERSION} nifi-registry-current && \
    rm nifi-registry-${NIFI_VERSION}-bin.zip

RUN mkdir -p /opt/nifi/nifi-registry-current/scripts

USER nifi

COPY scripts ${NIFI_REGISTRY_HOME}/scripts
COPY authorizers.xml ${NIFI_REGISTRY_HOME}/conf/authorizers.xml

USER root
RUN chmod -R +x ${NIFI_REGISTRY_HOME}/scripts
RUN chown -R nifi: ${NIFI_REGISTRY_HOME}

USER nifi
WORKDIR ${NIFI_REGISTRY_HOME}

ENTRYPOINT ["/opt/nifi/nifi-registry-current/scripts/start-nifi-registry.sh"]