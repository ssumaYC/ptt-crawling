FROM python:3.7.0

COPY ./* /usr/spiderkeeper/
WORKDIR /usr/spiderkeeper/
RUN pip install -r requirements.txt
ENTRYPOINT [ "spiderkeeper" ]
CMD [ "--server=http://10.140.0.9:6800", "--server=http://10.140.0.9:6800" ]
