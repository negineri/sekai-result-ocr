FROM python:3.9-slim
LABEL maintainer="harusoin@gmail.com"
ARG DEBIAN_FRONTEND=noninteractive
ENV PIPENV_VENV_IN_PROJECT 1
WORKDIR /opt/sekai-result-ocr
RUN apt-get -q -y update \
  && apt-get -q -y -o "DPkg::Options::=--force-confold" -o "DPkg::Options::=--force-confdef" install git \
    tesseract-ocr-jpn \
  && apt-get -q -y autoremove \
  && apt-get -q -y clean \
  && rm -rf /var/lib/apt/lists/* \
  && git clone git@github.com:negineri/sekai-result-ocr.git . \
  && pip install --upgrade pip \
  && pip install pipenv \
  && pipenv install
ENTRYPOINT [ "gunicorn", "main:app" ]
CMD [ "-c", "gunicorn_settings.py" ]