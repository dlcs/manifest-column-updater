FROM python:3.13-slim-bookworm

COPY requirements.txt /opt/app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt --target /opt/app/

COPY *.py /opt/app
COPY app/*.py /opt/app/app

ENTRYPOINT ["python3"]