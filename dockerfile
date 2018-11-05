FROM python:3-stretch
MAINTAINER Daniel Winks


COPY pwrstat-api.py requirements.txt powerpanel_*_amd64.deb init.sh /

RUN chmod +x /init.sh && chmod +x /pwrstat-api.py 
RUN pip install --trusted-host pypi.python.org -r requirements.txt
RUN dpkg -i powerpanel_*_amd64.deb

ENTRYPOINT "/init.sh"