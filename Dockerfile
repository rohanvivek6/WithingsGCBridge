FROM python:3.10-alpine

RUN apk update
RUN apk add git

# install dependencies
RUN mkdir /app
COPY ./requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

# copy application
COPY ./main.py ./bridge.py ./config.py ./models.py /app/
COPY ./withings /app/withings
COPY ./garmin /app/garmin

WORKDIR /app

# set entrypoint
ENTRYPOINT [ "python", "main.py"]
