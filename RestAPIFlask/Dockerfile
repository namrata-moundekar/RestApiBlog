# syntax=docker/dockerfile:1
FROM python:3.9

WORKDIR /RestAPIFlask
COPY requirements.txt /RestAPIFlask/
RUN pip install -r requirements.txt
COPY . /RestAPIFlask/
EXPOSE 5000
CMD python view.py











