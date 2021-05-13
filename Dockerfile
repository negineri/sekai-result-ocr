FROM python:3.9-slim
LABEL maintainer="harusoin@gmail.com"
ARG DEBIAN_FRONTEND=noninteractive
ENV PIPENV_VENV_IN_PROJECT 1
WORKDIR /opt/sekai-result-ocr
RUN apt-get -q -y update \
  && apt-get -q -y -o "DPkg::Options::=--force-confold" -o "DPkg::Options::=--force-confdef" install git wget gnupg\
  && echo "deb https://notesalexp.org/tesseract-ocr/buster/ buster main" >> /etc/apt/sources.list \
  && wget -O - https://notesalexp.org/debian/alexp_key.asc | apt-key add - \
  && apt-get -q -y update \
  && apt-get -q -y -o "DPkg::Options::=--force-confold" -o "DPkg::Options::=--force-confdef" install tesseract-ocr \
  && apt-get -q -y autoremove \
  && apt-get -q -y clean \
  && rm -rf /var/lib/apt/lists/* \
  && wget https://github.com/tesseract-ocr/tessdata_best/raw/master/eng.traineddata \
  && mv eng.traineddata /usr/share/tesseract-ocr/4.00/tessdata/ \
  && wget https://github.com/tesseract-ocr/tessdata_best/raw/master/jpn.traineddata \
  && mv jpn.traineddata /usr/share/tesseract-ocr/4.00/tessdata/ \
  && git clone https://github.com/negineri/sekai-result-ocr.git . \
  && pip install --upgrade pip \
  && pip install pipenv \
  && pipenv install --system
EXPOSE 80
ENTRYPOINT ["gunicorn", "main:app" ]
CMD [ "-c", "gunicorn_settings.py" ]