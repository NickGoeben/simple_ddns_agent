FROM python:3

RUN pip3 install boto3 requests awscli

ADD ddns.py /

CMD [ "python3", "./ddns.py" ]
