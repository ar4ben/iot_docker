# BUILD IMAGE
FROM arm32v6/python:2.7-alpine3.7 as builder

RUN apk --no-cache add git build-base

WORKDIR /home
RUN git clone https://github.com/adafruit/Adafruit_Python_DHT.git && \
	cd Adafruit_Python_DHT && \
	python setup.py install

## RUNTIME IMAGE
FROM arm32v6/python:2.7-alpine3.7

RUN apk --no-cache add ca-certificates

COPY --from=builder /usr/local/lib/python2.7 /usr/local/lib/python2.7

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt
COPY app.py /app/app.py
ENTRYPOINT ["python","-u","app.py"]
