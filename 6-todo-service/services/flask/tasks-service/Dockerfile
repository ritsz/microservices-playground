FROM python:3-alpine

COPY ./requirements.txt /tmp/requirements.txt
RUN pip3 install --upgrade pip && pip3 install --no-cache-dir -r /tmp/requirements.txt
COPY tasks-service.py /var/server/tasks-service.py

CMD python /var/server/tasks-service.py
