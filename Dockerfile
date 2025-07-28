FROM python:3.10.8
LABEL maintainer="b4oody"

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app/


COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt


COPY . .

RUN adduser \
    --disabled-password \
    --no-create-home \
    my_user

RUN mkdir -p /app/staticfiles /app/media
RUN chown -R my_user:my_user /app


USER my_user
