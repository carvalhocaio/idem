import sys

sys.path.append(".")
import env

import oci


class OracleCloudInfrastructure:
    def __init__(self):
        self.config = env.ORACLE_CLOUD_INFRASTRUCTURE_CONFIG
        self.comparment_id = env.ORACLE_CLOUD_INFRASTRUCTURE_COMPARTMENT_ID
        self.compute_client = oci.core.ComputeClient(config=self.config)
