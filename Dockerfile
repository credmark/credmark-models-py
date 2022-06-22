FROM python:3.10

WORKDIR /usr/local/app

COPY . .
RUN pip install -r requirements.txt -r requirements-dev.txt

CMD [ "credmark-dev" ]