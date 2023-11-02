# syntax=docker/dockerfile:1.4
FROM python:3.7 AS builder
WORKDIR /code

COPY . /code

RUN pip install --upgrade pip

# COPY ./.docker/checkinstall.txt /code

# RUN cat /code/checkinstall.txt >> /etc/apt/sources.list

USER root
RUN apt-get update

RUN  apt-get install build-essential checkinstall

RUN apt-get install -y libeditreadline-dev libncursesw5-dev libssl-dev \
    libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev libffi-dev zlib1g-dev

RUN pip3 install -r requirements.txt

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
