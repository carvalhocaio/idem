import oci


class OracleCloudInfrastructure:
    def __init__(
        self, compute_client: oci.core.ComputeClient, compartment_id: str
    ):
        self.compute_client = compute_client
        self.compartment_id = compartment_id
