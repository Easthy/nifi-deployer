#!/bin/sh -e

scripts_dir='/opt/nifi/scripts'

[ -f "${scripts_dir}/common.sh" ] && . "${scripts_dir}/common.sh"

# Establish baseline properties
prop_replace 'nifi.web.https.port'              "${NIFI_WEB_HTTPS_PORT:-8443}"
prop_replace 'nifi.web.https.host'              "${NIFI_WEB_HTTPS_HOST:-$HOSTNAME}"
prop_replace 'nifi.remote.input.host'           "${NIFI_REMOTE_INPUT_HOST:-$HOSTNAME}"
prop_replace 'nifi.remote.input.socket.port'    "${NIFI_REMOTE_INPUT_SOCKET_PORT:-10000}"
prop_replace 'nifi.remote.input.secure' 'true'

prop_replace 'nifi.security.keystore'           "${KEYSTORE_PATH}"
prop_replace 'nifi.security.keystoreType'       "${KEYSTORE_TYPE}"
prop_replace 'nifi.security.keystorePasswd'     "$(cat $TOOLKIT_CERTIFICATE_FOLDER/nifi.properties | grep "nifi.security.keystorePasswd" | awk -F\= '{gsub(/"/,"",$2);print $2}')"
prop_replace 'nifi.security.keyPasswd'          "$(cat $TOOLKIT_CERTIFICATE_FOLDER/nifi.properties | grep "nifi.security.keyPasswd" | awk -F\= '{gsub(/"/,"",$2);print $2}')"
prop_replace 'nifi.security.truststore'         "${TRUSTSTORE_PATH}"
prop_replace 'nifi.security.truststoreType'     "${TRUSTSTORE_TYPE}"
prop_replace 'nifi.security.truststorePasswd'   "$(cat $TOOLKIT_CERTIFICATE_FOLDER/nifi.properties | grep "nifi.security.truststorePasswd" | awk -F\= '{gsub(/"/,"",$2);print $2}')"
prop_replace 'nifi.security.user.authorizer'    "managed-authorizer"
prop_replace 'nifi.security.user.login.identity.provider'    ""



# Establish initial user and an associated admin identity
sed -i -e 's|<property name="Initial User Identity 1"></property>|<property name="Initial User Identity 1">'"${INITIAL_ADMIN_IDENTITY}"'</property>|'  ${NIFI_HOME}/conf/authorizers.xml
sed -i -e 's|<property name="Initial Admin Identity"></property>|<property name="Initial Admin Identity">'"${INITIAL_ADMIN_IDENTITY}"'</property>|'  ${NIFI_HOME}/conf/authorizers.xml

# Continuously provide logs so that 'docker logs' can    produce them
"${NIFI_HOME}/bin/nifi.sh" run &
nifi_pid="$!"
tail -F --pid=${nifi_pid} "${NIFI_HOME}/logs/nifi-app.log" &

trap 'echo Received trapped signal, beginning shutdown...;./bin/nifi.sh stop;exit 0;' TERM HUP INT;
trap ":" EXIT

echo NiFi running with PID ${nifi_pid}.
wait ${nifi_pid}