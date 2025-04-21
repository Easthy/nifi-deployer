#!/bin/bash

CURRENT_USER=$(whoami)

# Build/rebuild image
./build.sh

# Create directory for certs
mkdir -p ./keys

# Start NiFi & NiFi Registry
docker-compose -f docker-compose.yml up -d

# Copy certs from docker volume
sudo cp -r /var/lib/docker/volumes/nifi-certs/_data/auth-certs-san/ ./keys && chown -R $CURRENT_USER:$CURRENT_USER ./keys

# Generate certificate files for nypyapi
echo "generating certificates for nipyapi..."
USER_CERT_FILE=$(find . -type f -name "*.p12")
USER_CERT_FILE_PASSWORD=$(find . -type f -name "*.password")
LOCALHOST_TRUSTSTORE_JKS=$(find . -type f -name "truststore.jks")
LOCALHOST_NIFI_PROPERTIES_FILE=$(find . -type f -name "nifi.properties")
LOCALHOST_TRUSTSTORE_JKS_PASSWORD=$(cat $LOCALHOST_NIFI_PROPERTIES_FILE | grep "nifi.security.truststorePasswd" | awk -F\= '{gsub(/"/,"",$2);print $2}')

DIR_FOR_EXPORTED_CERT="./keys/nipyapi"
mkdir -p $DIR_FOR_EXPORTED_CERT

# create a Java Key Store (JKS) from the client key (client-ks.jks file)
keytool -importkeystore \
  -srckeystore $USER_CERT_FILE -srcstoretype PKCS12 -srcstorepass $(cat $USER_CERT_FILE_PASSWORD) \
  -destkeystore $DIR_FOR_EXPORTED_CERT/client-ks.jks -deststoretype JKS -deststorepass 'nipyapi' -destkeypass 'nipyapi'

# copy keys and certificates from JKS format into PKCS12 format (creates client-ks.p12 file):
keytool -importkeystore \
  -srckeystore $DIR_FOR_EXPORTED_CERT/client-ks.jks -srcstoretype jks -srcstorepass 'nipyapi' \
  -destkeystore $DIR_FOR_EXPORTED_CERT/client-ks.p12 -deststoretype pkcs12 -deststorepass 'nipyapi'

# creates localhost-ts.p12 from truststore.jks file (localhost)
keytool -importkeystore \
  -srckeystore $LOCALHOST_TRUSTSTORE_JKS -srcstoretype jks -srcstorepass $LOCALHOST_TRUSTSTORE_JKS_PASSWORD \
  -destkeystore $DIR_FOR_EXPORTED_CERT/localhost-ts.p12 -deststoretype pkcs12 -deststorepass 'nipyapi'

# copy the CA certificate from PKCS12 format to PEM format:
openssl pkcs12 -in $DIR_FOR_EXPORTED_CERT/localhost-ts.p12 -passin pass:'nipyapi' -out $DIR_FOR_EXPORTED_CERT/localhost-ts.pem -nokeys
openssl pkcs12 -in $DIR_FOR_EXPORTED_CERT/client-ks.p12 -passin pass:'nipyapi' -out $DIR_FOR_EXPORTED_CERT/client-cert.pem -nokeys
openssl pkcs12 -in $DIR_FOR_EXPORTED_CERT/client-ks.p12 -passin pass:'nipyapi' -out $DIR_FOR_EXPORTED_CERT/client-key.pem -passout pass:'nipyapi' 
echo "certificates for nipyapi created"
