#!/usr/bin/env python3
"""Get output from pwrstat program and send results to REST or MQTT clients."""
from typing import Dict
import json
import subprocess
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
        self.mqtt_config = kwargs["mqtt_config"]
        self.client = mqtt.Client(
            client_id="pwrstat_mqtt",
            clean_session=True,
            userdata=None,
            protocol=mqtt.MQTTv311,
            transport="tcp",
        )
        mqtt_host = self.mqtt_config["broker"]
        mqtt_port = self.mqtt_config["port"]
        self.client.connect_async(host=mqtt_host, port=mqtt_port)
        self.client.conn
        schedule.every(self.mqtt_config["refresh"]).seconds.do(self.publish_update)

    def publish_update(self):
        """Update MQTT topic with latest status."""
        status = get_status()
        print(status)
        json_payload = json.dumps(status)
        rc = self.client.publish(
            self.mqtt_config["topic"],
            json_payload,
            qos=self.mqtt_config["qos"],
            retain=self.mqtt_config["retained"],
        )
        print(rc.is_published())


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
            if "mqtt" in yaml_config:
                self.mqtt_config = yaml_config.get("mqtt")
            if "rest" in yaml_config:
                self.rest_config = yaml_config.get("rest")

        mqtt_schema = vol.Schema(
            {
                vol.Required("broker"): vol.All(str, vol.Length(min=7, max=15), vol.Match(VALID_IP_REGEX)),
                vol.Required("port"): int,
                vol.Required("topic"): str,
                vol.Required("refresh"): int,
                vol.Required("qos"): int,
                vol.Required("retained"): bool,
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
            print(self.mqtt_config)
            mqtt_schema(self.mqtt_config)
            PwrstatMqtt(mqtt_config=self.mqtt_config)

        if self.rest_config is not None:
            rest_schema(self.rest_config)
            API.add_resource(PwrstatRest, "/pwrstat")
            APP.run(port=self.rest_config["port"], host=self.rest_config["bind_address"])


def get_status() -> Dict[str, str]:
    """Return status from pwrstat program.

    Returns:
        Dict[str, str] -- Dictionary containing status from pwrstat.

    """
    status = subprocess.Popen(["pwrstat", "-status"], stdout=subprocess.PIPE).communicate()[0].decode("utf-8")
    status_list = []
    for line in status.splitlines():
        line = line.lstrip()
        line = line.replace(". ", ";")
        line = line.replace(".", "")
        line = line.split(";")
        if len(line) > 1:
            status_list.append(line)
    return {k[0]: k[1] for k in status_list}


if __name__ == "__main__":
    Pwrstat()
