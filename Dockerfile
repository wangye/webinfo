FROM python:3.10-alpine

RUN mkdir /app
WORKDIR /app
ADD requirements.txt /app
RUN pip3 install -r requirements.txt
ADD . /app
USER nobody
EXPOSE 5000
ENTRYPOINT ["gunicorn", "--config", "gunicorn_config.py", "app.wsgi:app"]