FROM python:3.9

EXPOSE 5000

WORKDIR /app

RUN apt-get update -y && \
    apt-get install -y python-dev libpq-dev

COPY ./requirements.txt ./requirements.txt
RUN python -m pip install --upgrade pip setuptools wheel \
    && python -m pip install -r requirements.txt

COPY ./twetty/ ./
