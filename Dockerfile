FROM python:3.9

EXPOSE 5000

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update -y && \
    apt-get install -y python-dev-is-python3 libpq-dev

COPY ./tweetty/tweetty_cli/main.sh /usr/bin/tweetty_cli

COPY ./requirements.txt ./requirements.txt
RUN python -m pip install --upgrade pip setuptools wheel \
    && python -m pip install -r requirements.txt \
    && rm -rf /root/.cache/pip

COPY ./tweetty ./tweetty
