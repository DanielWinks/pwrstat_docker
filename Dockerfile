FROM python:3.8-slim
LABEL Description="CyberPower PowerPanel"
LABEL Maintainer="Daniel Winks"

COPY *.py requirements.txt PPL_64bit_v1.4.2.deb init.sh pwrstat.yaml /

RUN apt-get update && apt-get dist-upgrade -y && \
    apt-get install -y procps && \
    apt-get install -y curl && \
    chmod +x /init.sh && chmod +x /pwrstat_api.py && \
    pip install --trusted-host pypi.python.org -r requirements.txt && \
    apt-get install -y /PPL_64bit_v1.4.2.deb && \
    apt-get -y --purge autoremove && apt-get clean && \
    rm -rf /tmp/* /var/tmp/* /var/lib/apt/lists/* /PPL_64bit_v1.4.2.deb

CMD ["/init.sh"]
