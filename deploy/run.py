import nipyapi
import argparse
from logzero import logger
from helper import *
from pathlib import Path


class NiFi():
    """NiFi deploy"""
    def __init__(self, kwargs):
        super(NiFi, self).__init__()
        kwargs = vars(kwargs)
        if len(kwargs) == 0:
            sys.exit("No deploy configuration parameters were passed")
        with open(kwargs['deploy_config'], 'r') as conf_stream:
            kwargs.update(yaml.safe_load(conf_stream))
            self.__dict__.update(kwargs)
        
    def _set_nifi_connection(self, environment=None):
        if not environment:
            raise Exception("Choose environment")
        logger.info(f'Connecting to {environment} environment')
        server_cert = "/".join((self.keys_folder, getattr(self, environment).get('server_cert'),))
        client_cert_file = "/".join((self.keys_folder, getattr(self, environment).get('client_cert'),))
        client_key_file = "/".join((self.keys_folder, getattr(self, environment).get('client_key'),))
        client_key_file_password = getattr(self, environment).get('client_key_password')

        nipyapi.utils.set_endpoint(getattr(self, environment).get('nifi_api_url'))
        nipyapi.utils.set_endpoint(getattr(self, environment).get('registry_api_url'))

        nipyapi.security.set_service_ssl_context(
            service='nifi',
            ca_file=server_cert,
            client_cert_file=client_cert_file,
            client_key_file=client_key_file,
            client_key_password=client_key_file_password
        )
        nipyapi.security.set_service_ssl_context(
            service='registry',
            ca_file=server_cert,
            client_cert_file=client_cert_file,
            client_key_file=client_key_file,
            client_key_password=client_key_file_password
        )

    def _start_deploy(self):
        logger.info(f"""Deploy {self.flow_name_from} at version {self.flow_version or 'latest'}"""
                    f""" from {self.bucket_from} development bucket"""
                    f""" to {self.bucket_to} production bucket"""
                    f""" with {self.flow_name_to} flow name"""
                    f""" using {self.deploy_config} connection config file"""
        )
        if not ask_yesno():
            exit("Deploy cancelled")

        # Export flow
        encoded_flow_to_deploy = self._export_flow('develop', self.bucket_from, self.flow_name_from)

        # Deploy
        self._set_nifi_connection(environment='production')
        bucket = self._get_or_create_bucket('production', self.bucket_to)
        flow = self._get_or_create_flow('production', self.bucket_to, self.flow_name_to)
        # Import exported flow
        nipyapi.versioning.import_flow_version(
            bucket.identifier, 
            encoded_flow=encoded_flow_to_deploy, 
            flow_id=flow.identifier
        )
        # Find root process group to deploy to
        root_pg_id = nipyapi.canvas.get_root_pg_id()
        logger.info(f'Root production process group {root_pg_id}')

        # Coordinates of Deployed process group
        location = (200, 200)

        # Find production registry id
        nifi_registry_name = getattr(self, 'production').get('registry_name')
        registry_to_id = nipyapi.versioning.get_registry_client(nifi_registry_name).id
        logger.info(f'Using production registry with id: {registry_to_id}')

        # Get latest flow version
        flow_version = nipyapi.versioning.get_latest_flow_ver(bucket.identifier, flow.identifier).flow.version_count

        # Check if flow already existed
        process_group_entity = nipyapi.canvas.get_process_group(str(self.flow_name_to), identifier_type='name', greedy=True)

        if not process_group_entity:
            logger.warning("Flow has not been added to canvas. First deployment")
            # Deploy
            process_group_entity = nipyapi.versioning.deploy_flow_version(
                root_pg_id, 
                location, 
                bucket.identifier, 
                flow.identifier, 
                registry_to_id,
                version=flow_version
            )
            logger.info(f"{f'Successfull {process_group_entity.id}' if (process_group_entity and process_group_entity.id is not None) else 'failed'} deployment")

            # Set PG name after deploy
            nipyapi.canvas.update_process_group(process_group_entity, {"name": f"{self.flow_name_to}"})
        else:
            logger.warning("Flow has been already added to canvas. Change version to the latest")
            result = nipyapi.versioning.update_flow_ver(process_group_entity, target_version=self.flow_version)
            logger.info("Successfully changed version" if result else 'Failed to upgrade flow version')

        # Set values for parametr context
        self._set_parameters()


    def _set_parameters(self):
        if not Path(self.parameter_context).is_file():
            logger.info("No parameter context to set. Deploy has been ended")
            return True

        def _get_by_name_or_create_parameter_context(parameter_context_name):
            logger.info(f'Searching for parameter context named as {parameter_context_name}')
            parameter_context = nipyapi.parameters.get_parameter_context(parameter_context_name, identifier_type='name', greedy=False)
            if parameter_context is None:
                logger.info('Parameter context does not exists. Creating...')
                return nipyapi.parameters.create_parameter_context(
                    name=parameter_context_name,
                    description=f"Parameter context created during deployment for the {self.bucket_to}:{self.flow_name_to}",
                    parameters=[]
                )
            return parameter_context

        self._set_nifi_connection(environment='production')

        with open(self.parameter_context, 'r') as parameter_context_stream:
            parameter_config = yaml.safe_load(parameter_context_stream)

            for context in parameter_config:
                parameter_context = _get_by_name_or_create_parameter_context(context.get('name'))
                logger.info(f"Creating/updating parameters in parameter context: {context.get('name')}")
                for param_name, param_data in context.get('parameters').items():
                    parameter = nipyapi.parameters.prepare_parameter(
                            name=param_name,
                            value=param_data.get("value", None),
                            sensitive=param_data.get("sensitive", None),
                            description=param_data.get("description", None)
                        )
                    parameter = nipyapi.parameters.upsert_parameter_to_context(context=parameter_context, parameter=parameter)

                if context.get('assign_to_process_group', None):
                    process_group_entity = nipyapi.canvas.get_process_group(str(context.get('assign_to_process_group')), identifier_type='name', greedy=True)

                    logger.info(f'Assigning parameter context to process group {process_group_entity.id}')
                    nipyapi.parameters.assign_context_to_process_group(
                        pg=process_group_entity,
                        context_id=parameter_context.id,
                        cascade=False
                    )

    def _export_flow(self,
                     environment,
                     bucket_from, 
                     flow_name_from):
        # Find versioned bucket & flow
        bucket, flow = self._get_bucket_flow(environment, bucket_from, flow_name_from)
        if not bucket or not flow:
            raise Exception('Bucket or flow can not be found')

        # Export flow
        logger.info(f'Exporting flow from {environment} registry')
        self._set_nifi_connection(environment=environment)
        encoded_flow_to_deploy = nipyapi.versioning.export_flow_version(
            bucket.identifier, 
            flow.identifier, 
            mode='json'
        )
        logger.info('Flow was exported successfully')
        return encoded_flow_to_deploy

    def _get_bucket(self, environment, bucket_name):
        self._set_nifi_connection(environment=environment)
        return nipyapi.versioning.get_registry_bucket(
            str(bucket_name), 
            identifier_type='name'
        )

    def _get_bucket_flow(self, 
                         environment, 
                         bucket_name,
                         flow_name):
        bucket = self._get_bucket(environment, bucket_name)
        if not bucket:
            raise Exception('Bucket can not be found')
        self._set_nifi_connection(environment=environment)
        flow = nipyapi.versioning.get_flow_in_bucket(
            bucket.identifier, 
            str(flow_name), 
            identifier_type='name'
        )
        return bucket, flow

    def _get_or_create_bucket(self, environment, bucket_name):
        bucket = self._get_bucket(environment, bucket_name)
        if bucket is None:
            logger.info('Bucket does not exist. Creating')
            self._set_nifi_connection(environment=environment)
            bucket = nipyapi.versioning.create_registry_bucket(bucket_name)
        return bucket

    def _get_or_create_flow(self, environment, bucket_name, flow_name):
        bucket, flow = self._get_bucket_flow(environment, bucket_name, flow_name) 

        if flow is None:
            logger.info('Flow does not exist. Creating')
            flow = nipyapi.versioning.create_flow(
                bucket.identifier, 
                flow_name, 
                flow_desc='Created during deployment', 
                flow_type='Flow'
            )
        return flow


if __name__ == "__main__":
    """ This is executed when run from the command line """
    parser = argparse.ArgumentParser()
    parser.add_argument("--bucket_from", type=str, required=True,
                        help="Development NiFi Registry bucket name")
    parser.add_argument("--bucket_to", type=str, required=True,
                        help="Production NiFi Registry bucket name")
    parser.add_argument("--flow_name_from", type=str, required=True,
                        help="Flow name at development NiFi Registry bucket")
    parser.add_argument("--flow_name_to", type=str, required=True,
                        help="Flow name at production NiFi Registry bucket")
    parser.add_argument("--flow_version", type=int, default=None,
                        help="Flow version to deploy (at development NiFi Registry bucket). None to retrieve the latest")
    parser.add_argument("--deploy_config", type=str, default="./deploy-config.yml",
                        help="Various configurations such NiFi connection, NiFi Registry connection, etc")
    parser.add_argument("--parameter_context", type=str, default="./parameter-context.yml",
                        help="Parameters used by NiFi processors")
    kwargs = parser.parse_args()
    NiFi(kwargs)._start_deploy()
