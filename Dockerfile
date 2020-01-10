FROM python:3.8-slim
LABEL Description="CyberPower PowerPanel"
LABEL Maintainer="Daniel Winks"

COPY pwrstat_api.py requirements.txt powerpanel_*_amd64.deb init.sh pwrstat.yaml /
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

RUN apt-get update && apt-get dist-upgrade -y && \
    apt-get install -y procps supervisor && \
    chmod +x /init.sh && chmod +x /pwrstat_api.py && \
    pip install --trusted-host pypi.python.org -r requirements.txt && \
    dpkg -i powerpanel_*_amd64.deb && \
    apt-get -y --purge autoremove && apt-get clean && \
    rm -rf /tmp/* /var/tmp/* /var/lib/apt/lists/*

CMD ["/usr/bin/supervisord"]
