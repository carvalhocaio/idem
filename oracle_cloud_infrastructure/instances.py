import time
from abc import ABC, abstractmethod

import oci
import streamlit as st

from typing import List, Any

import sys

from oci import Response

sys.path.append(".")
import env
from oracle_cloud_infrastructure import OracleCloudInfrastructure


class OracleCloudClient(OracleCloudInfrastructure):
    """Responsável por interagir com o cliente OCI."""

    def __init__(
        self, compute_client: oci.core.ComputeClient, compartment_id: str
    ):
        super().__init__(compute_client, compartment_id)

    def list_instances(self) -> list[Any] | Response:
        try:
            return self.compute_client.list_instances(self.compartment_id)
        except oci.exceptions.ServiceError as e:
            st.error(f"Error listing instances: {e.message}")
            return []

    def perform_instance_action(self, instance_id: str, action: str):
        try:
            self.compute_client.instance_action(instance_id, action.upper())
        except oci.exceptions.ServiceError as e:
            st.error(
                f"Error performing action '{action}' on instance: {e.message}"
            )
            raise


class InstanceStateHandler:
    """Gerencia a espera por mudanças de estado das instâncias."""

    def __init__(self, client: OracleCloudClient):
        self.client = client

    def wait_for_state(
        self, instance_id: str, target_state: str, interval: int = 10
    ):
        while (
            self.client.compute_client.get_instance(
                instance_id
            ).data.lifecycle_state
            != target_state
        ):
            st.info(f"Waiting for the instance state to be: {target_state}")
            time.sleep(interval)


class InstanceAction(ABC):
    """Interface para ações de instância."""

    @abstractmethod
    def execute(self, instance_data: dict):
        pass


class StartInstanceAction(InstanceAction):
    """Ação para iniciar uma instância."""

    def __init__(
        self, client: OracleCloudClient, state_handler: InstanceStateHandler
    ):
        self.client = client
        self.state_handler = state_handler

    def execute(self, instance_data: dict):
        instance_id = instance_data["id"]
        instance_name = instance_data["display_name"]
        st.info(f"Starting the instance [{instance_name}]...")

        self.client.perform_instance_action(instance_id, "start")
        self.state_handler.wait_for_state(instance_id, "RUNNING")
        st.success(f"Instance [{instance_name}] is now RUNNING!")


class StopInstanceAction(InstanceAction):
    """Ação para parar uma instância."""

    def __init__(
        self, client: OracleCloudClient, state_handler: InstanceStateHandler
    ):
        self.client = client
        self.state_handler = state_handler

    def execute(self, instance_data: dict):
        instance_id = instance_data["id"]
        instance_name = instance_data["display_name"]
        st.info(f"Stopping the instance [{instance_name}]...")

        self.client.perform_instance_action(instance_id, "stop")
        self.state_handler.wait_for_state(instance_id, "STOPPED")
        st.success(f"Instance [{instance_name}] is now STOPPED!")


class InstanceManager:
    """Gerencia a obtenção de dados das instâncias."""

    def __init__(self, client: OracleCloudClient):
        self.client = client

    def get_instances_data(self) -> List[dict]:
        instances = self.client.list_instances().data
        return [
            {
                "id": instance.id,
                "display_name": instance.display_name,
                "shape_memory_in_gbs": instance.shape_config.memory_in_gbs,
                "shape_ocpus": instance.shape_config.ocpus,
                "time_created": instance.time_created,
                "lifecycle_state": instance.lifecycle_state,
            }
            for instance in instances
        ]


def main():
    st.title("Monitoramento das instâncias da Oracle Cloud Infrastructure")
    st.divider()

    compute_client = oci.core.ComputeClient(
        config=env.ORACLE_CLOUD_INFRASTRUCTURE_CONFIG
    )
    compartment_id = env.ORACLE_CLOUD_INFRASTRUCTURE_COMPARTMENT_ID
    client = OracleCloudClient(compute_client, compartment_id)
    state_handler = InstanceStateHandler(client)
    instance_manager = InstanceManager(client)

    instances_data = instance_manager.get_instances_data()
    st.dataframe(
        data=instances_data,
        column_order=[
            "display_name",
            "shape_memory_in_gbs",
            "shape_ocpus",
            "time_created",
            "lifecycle_state",
        ],
        hide_index=True,
    )

    with st.sidebar:
        instance_names = [
            instance["display_name"] for instance in instances_data
        ]
        selected_instance_name = st.selectbox(
            "Select the instance", instance_names
        )
        selected_instance_data = next(
            (
                inst
                for inst in instances_data
                if inst["display_name"] == selected_instance_name
            ),
            None,
        )

        if selected_instance_data["lifecycle_state"] == "STOPPED":
            if st.button(
                "POWER ON", icon=":material/power:", use_container_width=True
            ):
                action = StartInstanceAction(client, state_handler)
                action.execute(selected_instance_data)
                time.sleep(2)
                st.rerun()

        if selected_instance_data["lifecycle_state"] == "RUNNING":
            if st.button(
                "POWER OFF",
                icon=":material/power_off:",
                use_container_width=True,
            ):
                action = StopInstanceAction(client, state_handler)
                action.execute(selected_instance_data)
                time.sleep(2)
                st.rerun()


if __name__ == "__main__":
    main()
