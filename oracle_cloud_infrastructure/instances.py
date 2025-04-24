import time
import oci
import streamlit as st

import sys

sys.path.append(".")
from oracle_cloud_infrastructure import OracleCloudInfrastructure

st.title("Monitoramento das instâncias da Oracle Cloud Infrastructure")
st.divider()


class Instances(OracleCloudInfrastructure):
    def __init__(self):
        super().__init__()

    def _wait_for_state(self, instance_id, target_state, interval):
        while (
            self.compute_client.get_instance(instance_id).data.lifecycle_state
            != target_state
        ):
            st.info(
                f"Waiting for the instance to reach the state {target_state}..."
            )
            time.sleep(interval)

    def get_instances(self):
        try:
            return self.compute_client.list_instances(self.comparment_id)
        except oci.exceptions.ServiceError as e:
            st.error(f"Error listing instances: {e.message}")

    def change_instance_state(
        self, instance_id, instance_name, action, target_state
    ):
        try:
            if action == "start":
                st.info(
                    f"{action.capitalize()}ing the instance [{instance_name}]"
                )
            if action == "stop":
                st.info(
                    f"{action.capitalize()}ping the instance [{instance_name}]"
                )

            self.compute_client.instance_action(instance_id, action.upper())
            self._wait_for_state(instance_id, target_state, interval=10)

            st.success(f"The state of instance [{instance_name}] was changed!")
        except oci.exceptions.ServiceError as e:
            st.error(
                f"Error to change state of instance [{instance_name}]: {e.message}"
            )

    @classmethod
    def list_instances(cls):
        return cls().get_instances()

    @classmethod
    def start_instance(cls, instance):
        return cls().change_instance_state(
            instance_id=instance["id"],
            instance_name=instance["display_name"],
            action="start",
            target_state="RUNNING",
        )

    @classmethod
    def stop_instance(cls, instance):
        return cls().change_instance_state(
            instance_id=instance["id"],
            instance_name=instance["display_name"],
            action="stop",
            target_state="STOPPED",
        )


instances = Instances.list_instances().data
instances_data = [
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
    instance_names = list(
        instance.get("display_name") for instance in instances_data
    )

    selected_instance = st.selectbox("Select the instance", instance_names)
    selected_instance_data = next(
        (
            inst
            for inst in instances_data
            if inst["display_name"] == selected_instance
        ),
        None,
    )

    if selected_instance_data["lifecycle_state"] == "RUNNING":
        if st.button(
            "POWER OFF",
            icon=":material/power_off:",
            use_container_width=True,
        ):
            Instances.stop_instance(instance=selected_instance_data)
            time.sleep(2)
            st.rerun()

    if selected_instance_data["lifecycle_state"] == "STOPPED":
        if st.button(
            "POWER ON",
            icon=":material/power:",
            use_container_width=True,
        ):
            Instances.start_instance(instance=selected_instance_data)
            time.sleep(2)
            st.rerun()
