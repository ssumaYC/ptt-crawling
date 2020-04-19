FROM vimagick/scrapyd:py3

COPY ./* /usr/
WORKDIR /usr/
RUN pip install -r requirements.txt
ENTRYPOINT [ "scrapyd", "--pidfile=" ]
