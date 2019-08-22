# PowerPanel (pwrstat) API & MQTT container

This is a container for the CyberPower 'pwrstat' utility.
Basic GET support for a single JSON object response for
all parameters of the UPS are implemented.
MQTT is also supported, with broker, port, and topic
options all being specified in the config file.

## Usage

### Example docker-compose

```yaml
    ---
    version: '2.4'
    services:
        pwr_stat:
            container_name: pwr_stat
            hostname: pwr_stat
            restart: always
            image: dwinks/pwrstat_docker:latest
            devices:
                - /dev/bus/usb/003/003:/dev/bus/usb/001/001
            volumes:
                - /docker_binds/pwr_stat/pwrstat.yaml:/pwrstat.yaml:ro
            healthcheck:
                test: ["CMD", "curl", "-sI", "http://127.0.0.1:5002/pwrstat"]
                interval: 30s
                timeout: 1s
                retries: 24
            privileged: true
            network_mode: host

```

### Example config file

```yaml
    ---
    mqtt:
        broker: "192.168.1.100"
        port: 1883
        topic: "sensors/basement/power/ups"
        refresh: 3
        qos: 0
        retained: true
    rest:
        port: 5003
        bind_address: "0.0.0.0"
```
