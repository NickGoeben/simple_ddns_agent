FROM python:3

RUN pip3 install boto3 requests awscli

ADD ddns-docker.py /
ADD ddns-test.py /

CMD [ "python3", "./ddns-it.py" ]
