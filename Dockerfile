FROM python:3.5

RUN apt-get update && apt-get install -y poppler-utils

COPY requirements.txt /app/requirements.txt

COPY server.py /app/server.py
COPY transform /app/transform
COPY startup.sh /app/startup.sh

RUN mkdir -p /app/tmp

# set working directory to /app/
WORKDIR /app/

EXPOSE 5000

RUN pip3 install --no-cache-dir -U -I -r /app/requirements.txt

ENTRYPOINT ./startup.sh
