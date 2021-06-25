# Heroku Dockerfile Sample
# https://github.com/heroku/alpinehelloworld
# FROM alpine:latest
FROM python:3.8-buster
# RUN apk add --no-cache --update python3 py3-pip bash
ADD ./requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -q -r /tmp/requirements.txt
ADD . /opt/contactupdate/
WORKDIR /opt/contactupdate
RUN adduser --disabled-password rani_as
USER rani_as
CMD python3 main.py