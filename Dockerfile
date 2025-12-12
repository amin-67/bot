FROM python:3.11-bullseye
RUN mkdir /pdf && chmod 777 /pdf

WORKDIR /ILovePDF

RUN apt-get update && apt-get install -y \
  git \
  ocrmypdf \
  wkhtmltopdf \
  tree \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY /ILovePDF .

RUN tree

CMD bash run.sh
