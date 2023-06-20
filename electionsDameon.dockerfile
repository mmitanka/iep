FROM python:3

RUN mkdir -p /opt/src/elections

WORKDIR /opt/src/elections

COPY elections/applicationDameon.py ./applicationDameon.py
COPY elections/configuration.py ./configuration.py
COPY elections/models.py ./models.py
COPY elections/requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt
#ENTRYPOINT [ "sleep" , "1200"]
ENV PYTHONPATH="/opt/src/elections"
ENTRYPOINT ["python","./applicationDameon.py"]