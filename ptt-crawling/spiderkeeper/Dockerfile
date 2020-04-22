FROM python:3.7.0

COPY ./* /usr/spiderkeeper/
WORKDIR /usr/spiderkeeper/
RUN pip install -r requirements.txt
ENTRYPOINT [ "spiderkeeper" ]
CMD [ "--server=http://spider1:6800", "--server=http://spider2:6800" ]
