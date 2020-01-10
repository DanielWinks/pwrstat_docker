#!/usr/bin/env python3
"""Create MQTT publisher."""
import asyncio
import json
import logging
from typing import Any, Dict, Optional

import paho.mqtt.client as mqtt

import pwrstat_api

LOGGER = logging.getLogger(__name__)
CLIENT = mqtt.Client()


class PwrstatMqtt:
    """Create MQTT publisher."""

    def __init__(self, mqtt_config: Dict[str, Any]) -> None:
        """Start MQTT loop."""
        self.mqtt_config = mqtt_config
        client_id: Optional[str] = self.mqtt_config.get("client_id")
        if client_id:
            CLIENT.reinitialise(client_id=client_id)

        username = self.mqtt_config.get("username")
        password = self.mqtt_config.get("password")
        if None not in (username, password):
            CLIENT.username_pw_set(username=username, password=password)

        mqtt_host: str = self.mqtt_config["broker"]
        mqtt_port: int = self.mqtt_config["port"]
        LOGGER.log(level=logging.INFO, msg="Connecting to MQTT broker...")
        CLIENT.connect(host=mqtt_host, port=mqtt_port)
        self.refresh_interval: int = self.mqtt_config["refresh"]

    async def loop(self) -> None:
        """Loop for MQTT updates."""
        LOGGER.log(level=logging.INFO, msg="Starting MQTT loop...")
        while True:
            await self.publish_update()
            LOGGER.log(level=logging.DEBUG, msg="Publishing message to MQTT broker...")
            await asyncio.sleep(self.refresh_interval)

    async def publish_update(self) -> bool:
        """Update MQTT topic with latest status."""
        topic = self.mqtt_config["topic"]
        qos: int = self.mqtt_config["qos"]
        retain: bool = self.mqtt_config["retained"]
        status = pwrstat_api.get_status()
        if status is not None:
            json_payload = json.dumps(status)
            result = CLIENT.publish(topic, json_payload, qos=qos, retain=retain)
            return result.is_published()
        return False


def is_connected() -> bool:
    """Check connection to MQTT broker."""
    return CLIENT.is_connected()


if __name__ == "__main__":
    pass
