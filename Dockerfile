FROM python:3.11-slim

# Install minimal packages
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       netcat jq \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app

# Copy application files
COPY app ./app
COPY run.sh ./run.sh

RUN chmod +x /usr/src/app/run.sh /usr/src/app/app/wol_forwarder.py

ENV PYTHONUNBUFFERED=1

CMD ["/usr/src/app/run.sh"]
