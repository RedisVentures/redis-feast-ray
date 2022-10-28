FROM python:3.8-slim-buster

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN python3 -m pip install --upgrade pip setuptools wheel
RUN apt-get update && apt-get -y install make

WORKDIR /app
COPY requirements.txt ./
COPY Makefile ./

RUN pip install -r requirements.txt
