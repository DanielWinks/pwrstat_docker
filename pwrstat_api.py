#!/usr/bin/env python3
"""Get output from pwrstat program and send results to REST or MQTT clients."""
from typing import Any, Dict, List, Optional
import json
import subprocess
import time
import threading
import schedule
import voluptuous as vol
import paho.mqtt.client as mqtt

from flask import Flask
from flask_jsonpify import jsonify
from flask_restful import Api, Resource
from ruamel.yaml import YAML as yaml, YAMLError

APP = Flask(__name__)
API = Api(APP)
YAML = yaml(typ="safe")

VALID_IP_REGEX = (
    r"^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.)"
    r"{3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$"
)


class PwrstatRest(Resource):
    """Create REST resource."""

    def get(self):
        """Responder for get requests.

        Returns:
            flask.Response -- Flask response with pwrstat info.

        """
        return jsonify(get_status())


class PwrstatMqtt:
    """Create MQTT publisher."""

    def __init__(self, *args, **kwargs) -> None:
        """Start MQTT loop.

        Returns: None
        """
        self.mqtt_config: Dict[str, Any] = kwargs["mqtt_config"]
        client_id: str = self.mqtt_config["client_id"]
        self.client = mqtt.Client(
            client_id=client_id,
            clean_session=True,
            userdata=None,
            protocol=mqtt.MQTTv311,
            transport="tcp",
        )

        username = self.mqtt_config.get("username")
        password = self.mqtt_config.get("password")
        if None not in (username, password):
            self.client.username_pw_set(username=username, password=password)

        mqtt_host: str = self.mqtt_config["broker"]
        mqtt_port: int = self.mqtt_config["port"]
        self.client.connect(host=mqtt_host, port=mqtt_port)

        refresh_interval: int = self.mqtt_config["refresh"]
        schedule.every(refresh_interval).seconds.do(self.publish_update)
        threading.Thread(target=self.run_jobs, daemon=True).start()

    # pylint: disable=R0201
    def run_jobs(self) -> None:
        """Run jobs on separate thread."""
        while True:
            schedule.run_pending()
            time.sleep(1)

    # pylint: enable=R0201

    def publish_update(self) -> None:
        """Update MQTT topic with latest status."""
        topic = self.mqtt_config["topic"]
        status = get_status()
        json_payload = json.dumps(status)
        qos: int = self.mqtt_config["qos"]
        retain: bool = self.mqtt_config["retained"]
        self.client.publish(topic, json_payload, qos=qos, retain=retain)


class Pwrstat:
    """Get output from pwrstat program and send results to REST or MQTT clients."""

    def __init__(self, *args, **kwargs) -> None:
        """Initilize Pwrstat class.

        Returns: None
        """
        with open("pwrstat.yaml") as file:
            try:
                yaml_config = YAML.load(file)
            except YAMLError as ex:
                print(ex)

        self.mqtt_config: Optional[Dict[str, Any]] = yaml_config[
            "mqtt"
        ] if "mqtt" in yaml_config else None
        self.rest_config: Optional[Dict[str, Any]] = yaml_config[
            "rest"
        ] if "rest" in yaml_config else None

        mqtt_schema = vol.Schema(
            {
                vol.Required("broker"): vol.All(
                    str, vol.Length(min=7, max=15), vol.Match(VALID_IP_REGEX)
                ),
                vol.Required("port"): int,
                vol.Required("client_id"): str,
                vol.Required("topic"): str,
                vol.Required("refresh"): int,
                vol.Required("qos"): int,
                vol.Required("retained"): bool,
                vol.Optional("username"): str,
                vol.Optional("password"): str,
            }
        )

        rest_schema = vol.Schema(
            {
                vol.Required("port"): vol.All(int, vol.Range(min=1025, max=65535)),
                vol.Required("bind_address"): vol.All(
                    str, vol.Length(min=7, max=15), vol.Match(VALID_IP_REGEX)
                ),
            }
        )

        if self.mqtt_config is not None:
            mqtt_schema(self.mqtt_config)
            PwrstatMqtt(mqtt_config=self.mqtt_config)

        if self.rest_config is not None:
            rest_schema(self.rest_config)
            API.add_resource(PwrstatRest, "/pwrstat")
            APP.run(
                port=self.rest_config["port"], host=self.rest_config["bind_address"]
            )


def get_status() -> Dict[str, str]:
    """Return status from pwrstat program.

    Returns:
        Dict[str, str] -- Dictionary containing status from pwrstat.

    """
    status: str = subprocess.Popen(
        ["pwrstat", "-status"], stdout=subprocess.PIPE
    ).communicate()[0].decode("utf-8")
    status_list: List[List[str]] = []
    for line in status.splitlines():
        line = line.lstrip()
        line = line.replace(". ", ";")
        line = line.replace(".", "")
        lines: List[str] = line.split(";")
        if len(lines) > 1:
            status_list.append(lines)
    return {k[0]: k[1] for k in status_list}


if __name__ == "__main__":
    Pwrstat()
