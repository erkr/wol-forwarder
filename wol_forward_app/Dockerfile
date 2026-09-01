FROM python:3.14-slim

ARG APP_IMAGE_TAG=undefined

# Install minimal packages
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       netcat-openbsd jq \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app

# Copy requirements and application files
COPY requirements.txt ./requirements.txt
COPY app ./app
COPY run.sh ./run.sh

RUN pip install --no-cache-dir -r requirements.txt \
    && chmod +x /usr/src/app/run.sh /usr/src/app/app/wol_forwarder.py

ENV PYTHONUNBUFFERED=1
ENV APP_IMAGE_TAG=$APP_IMAGE_TAG

CMD ["/usr/src/app/run.sh"]
