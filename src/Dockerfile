FROM python:3.13-slim-bookworm

COPY requirements.txt /opt/app/requirements.txt

RUN  pip install --no-cache-dir -r /opt/app/requirements.txt

COPY *.py /opt/app
COPY app/ /opt/app/app

ENTRYPOINT ["python", "/opt/app/manifest-column-updater.py"]