#### Create volume where you can access created certifaicates
```
docker volume create --name=nifi-certs
```

#### Remove dokcer volume if needed
docker-compose down --volumes
docker volume rm nifi-certs

## Build Docker images & export keys
```
./start.sh
```

#### Run NiFi & NiFi Registry locally
`docker-compose -f docker-compose.yml up`

#### Copy certificates from docker
`sudo cp /var/lib/docker/volumes/nifi-certs/_data/auth-certs-san/CN=admin_OU=NIFI.p12 ./CN=admin_OU=NIFI.p12`
`sudo cp /var/lib/docker/volumes/nifi-certs/_data/auth-certs-san/CN=admin_OU=NIFI.password ./CN=admin_OU=NIFI.password`
`sudo cp /var/lib/docker/volumes/nifi-certs/_data/auth-certs-san/localhost/keystore.jks ./keystore.jks`
`sudo cp /var/lib/docker/volumes/nifi-certs/_data/auth-certs-san/localhost/truststore.jks ./truststore.jks`
`sudo cp /var/lib/docker/volumes/nifi-certs/_data/auth-certs-san/nifi-cert.pem ./nifi-cert.pem`
`sudo cp /var/lib/docker/volumes/nifi-certs/_data/auth-certs-san/nifi-key.key ./nifi-key.key`


#### Check your jks password
```
keytool -list -v -keystore "./certs/keystore.jks"
```

#### Start NiFI toolkit cli
```
./bin/cli.sh
```

## Deploy from local NiFi to remote NiFi
The deploy folder contains the run.py script. In the same folder, there are two files:  

- deploy-config.yml — contains information about the location of the NiFi Registry in both the local and remote environments;  
- parameter-context.yml — defines the parameter contexts for each process group.  
During deployment, the flow is exported from the local NiFi Registry as a JSON file, then imported into the remote NiFi Registry. After that, the flow version is updated in Apache NiFi, and the parameters defined via parameter contexts are assigned or updated.

### Deployment
A bucket can contain more than one flow with different names at the same time. Flow in NiFi Registry is equivalent to Process Group in NiFi.  
NiFi nypyapi library documentation https://nipyapi.readthedocs.io/en/latest/nipyapi-docs/nipyapi.html#module-nipyapi.security