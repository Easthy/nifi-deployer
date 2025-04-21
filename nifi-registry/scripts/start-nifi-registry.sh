#!/bin/sh -e

scripts_dir="$NIFI_REGISTRY_HOME/scripts"

[ -f "${scripts_dir}/common.sh" ] && . "${scripts_dir}/common.sh"

# Establish baseline properties
prop_replace 'nifi.registry.web.https.port'     "${NIFI_REGISTRY_WEB_HTTPS_PORT:-8443}"
prop_replace 'nifi.registry.web.https.host'     "${NIFI_REGISTRY_WEB_HTTPS_HOST:-$HOSTNAME}"


prop_replace 'nifi.registry.security.keystore'           "${KEYSTORE_PATH}"
prop_replace 'nifi.registry.security.keystoreType'       "${KEYSTORE_TYPE}"
prop_replace 'nifi.registry.security.keystorePasswd'     "$(cat $TOOLKIT_CERTIFICATE_FOLDER/nifi.properties | grep "nifi.security.keystorePasswd" | awk -F\= '{gsub(/"/,"",$2);print $2}')"
prop_replace 'nifi.registry.security.keyPasswd'          "$(cat $TOOLKIT_CERTIFICATE_FOLDER/nifi.properties | grep "nifi.security.keyPasswd" | awk -F\= '{gsub(/"/,"",$2);print $2}')"
prop_replace 'nifi.registry.security.truststore'         "${TRUSTSTORE_PATH}"
prop_replace 'nifi.registry.security.truststoreType'     "${TRUSTSTORE_TYPE}"
prop_replace 'nifi.registry.security.truststorePasswd'   "$(cat $TOOLKIT_CERTIFICATE_FOLDER/nifi.properties | grep "nifi.security.truststorePasswd" | awk -F\= '{gsub(/"/,"",$2);print $2}')"
prop_replace 'nifi.registry.security.authorizer'         "managed-authorizer"
prop_replace 'nifi.registry.security.identity.provider'  ""
prop_replace 'nifi.registry.web.http.port'               ""

sed -i -e 's|<property name="Initial User Identity 1"></property>|<property name="Initial User Identity 1">'"${INITIAL_ADMIN_IDENTITY}"'</property>|'  ${NIFI_REGISTRY_HOME}/conf/authorizers.xml
sed -i -e 's|<property name="Initial Admin Identity"></property>|<property name="Initial Admin Identity">'"${INITIAL_ADMIN_IDENTITY}"'</property>|'  ${NIFI_REGISTRY_HOME}/conf/authorizers.xml


# Continuously provide logs so that 'docker logs' can    produce them
"${NIFI_REGISTRY_HOME}/bin/nifi-registry.sh" run &
nifi_registry_pid="$!"
tail -F --pid=${nifi_registry_pid} "${NIFI_REGISTRY_HOME}/logs/nifi-registry-app.log" &

trap 'echo Received trapped signal, beginning shutdown...;./bin/nifi-registry.sh stop;exit 0;' TERM HUP INT;
trap ":" EXIT

echo NiFi Registry running with PID ${nifi_registry_pid}.
wait ${nifi_registry_pid}