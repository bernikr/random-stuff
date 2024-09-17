FROM python:3.12-alpine

RUN which crond && rm -rf /etc/periodic

WORKDIR /src
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .

COPY crontab /var/spool/cron/crontabs/root

CMD ["crond", "-f", "-l", "2"]
