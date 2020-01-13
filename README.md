# PowerPanel (pwrstat) API & MQTT container

[![CircleCI](https://circleci.com/gh/DanielWinks/pwrstat_docker.svg?style=svg)](https://circleci.com/gh/DanielWinks/pwrstat_docker)

This is a container for the CyberPower 'pwrstat' utility.
Basic GET support for a single JSON object response for
all parameters of the UPS are implemented.
MQTT is also supported, with broker, port, client_id and topic
options all being specified in the config file. 
Optionally, username/password may be specified. 
TLS support soon.
Note: client_id must be unique.

## Usage

Available healthchecks: 
1) `http://server:port/health` <- `200 'OK'` if REST client functional
1) `http://server:port/mqtthealth` <- `200 'OK'` if MQTT client is connected to broker

### Example Kubernetes manifest

```yaml
---
apiVersion: v1
kind: Namespace
metadata:
  labels:
    app: pwrstat
  name: pwrstat

---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: pwrstat
  namespace: pwrstat
  labels:
    app: pwrstat
spec:
  replicas: 1
  serviceName: pwrstat
  selector:
    matchLabels:
      app: pwrstat
  template:
    metadata:
      labels:
        app: pwrstat
    spec:
      nodeSelector:
        kubernetes.io/hostname: my_host
      containers:
        - name: pwrstat
          securityContext:
            privileged: true
          image: dwinks/pwrstat_docker
          imagePullPolicy: "Always"
          livenessProbe:
            httpGet:
              path: /health
              port: 5003
            initialDelaySeconds: 10
            periodSeconds: 30
            failureThreshold: 5
          readinessProbe:
            httpGet:
              path: /health
              port: 5003
            initialDelaySeconds: 10
            periodSeconds: 30
            failureThreshold: 5
          startupProbe:
            httpGet:
              path: /health
              port: 5003
            initialDelaySeconds: 6
            periodSeconds: 6
            failureThreshold: 10
          resources:
            requests:
              cpu: "50m"
              memory: "50Mi"
            limits:
              cpu: "100m"
              memory: "100Mi"
          ports:
            - containerPort: 5003
          volumeMounts:
            - name: pwrstat-configmap
              mountPath: /pwrstat.yaml
              subPath: pwrstat.yaml
            - name: cyberpower-ups
              mountPath: /dev/bus/usb/001/001
              readOnly: false

      volumes:
        - name: pwrstat-configmap
          configMap:
            defaultMode: 0644
            name: pwrstat-configmap
            items:
              - key: pwrstat.yaml
                path: pwrstat.yaml
                mode: 0644
        - name: cyberpower-ups
          hostPath:
            path: /dev/bus/usb/003/002

---
apiVersion: v1
kind: Service
metadata:
  name: pwrstat
  namespace: pwrstat
  labels:
    app: pwrstat
spec:
  type: NodePort
  selector:
    app: pwrstat
  ports:
    - port: 5003
      targetPort: 5003
      name: http

---
apiVersion: v1
kind: ConfigMap
metadata:
  name: pwrstat-configmap
  namespace: pwrstat
data:
  pwrstat.yaml: |
    ---
    pwrstat_api:  # optional
      log_level: "DEBUG"  # optional
    mqtt:
      broker: "mosquitto.mosquitto"
      port: 1883
      client_id: "pwrstat_mqtt"
      topic: "sensors/basement/power/ups"
      refresh: 30
      qos: 0
      retained: true
      # username: "my_username" # optional
      # password: "my_password" # optional, required if username specified
    rest:
      port: 5003
      bind_address: "0.0.0.0"
```

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
            # Optionally override the powerstatd configuration file
            - /docker_binds/pwr_stat/pwrstatd.conf:/etc/pwrstatd.conf:ro
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
pwrstat_api: # optional
    log_level: WARNING # optional, may be 'DEBUG', 'WARNING', 'INFO', 'CRITICAL'
mqtt:
    broker: "192.168.1.100"
    port: 1883
    client_id: "pwrstat_mqtt"
    topic: "sensors/basement/power/ups"
    refresh: 3
    qos: 0
    retained: true
    # username: "my_username" # optional
    # password: "my_password" # optional, required if username specified
rest:
    port: 5002
    bind_address: "0.0.0.0"
```
