"""Schemas for Powerstat API."""

import voluptuous as vol

VALID_IP_REGEX = (
    r"^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.)"
    r"{3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$"
)

PWRSTAT_API_SCHEMA = vol.Schema({vol.Optional("log_level", default="WARNING"): str})

MQTT_SCHEMA = vol.Schema(
    {
        vol.Optional("broker", default="192.168.1.100"): str,
        vol.Optional("port", default=1883): int,
        vol.Optional("client_id", default="pwrstat_mqtt"): str,
        vol.Optional("topic", "sensors/basement/power/ups"): str,
        vol.Optional("refresh", default=30): int,
        vol.Optional("qos", default=0): int,
        vol.Optional("retained", default=True): bool,
        vol.Optional("username"): str,
        vol.Optional("password"): str,
    }
)

REST_SCHEMA = vol.Schema(
    {
        vol.Optional("port", default=5002): vol.All(
            int, vol.Range(min=1025, max=65535)
        ),
        vol.Optional("bind_address", default="0.0.0.0"): vol.All(
            str, vol.Length(min=7, max=15), vol.Match(VALID_IP_REGEX)
        ),
    }
)

PROMETHEUS_SCHEMA = vol.Schema(
    {
        vol.Optional("port", default=5002): vol.All(
            int, vol.Range(min=1025, max=65535)
        ),
        vol.Optional("bind_address", default="0.0.0.0"): vol.All(
            str, vol.Length(min=7, max=15), vol.Match(VALID_IP_REGEX)
        ),
        vol.Optional("labels", default={}): vol.All(
            dict
        ),
    }
)
