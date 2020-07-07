FROM python:3.7-alpine
ENV PYTHONUNBUFFERED 1
RUN mkdir /pyes
WORKDIR /pyes
RUN mkdir /pyes/data
RUN pip3 install --upgrade pip
RUN pip3 install elasticsearch==7.0.0 loguru
COPY . /pyes
ENTRYPOINT [ "python" ]
CMD [ "load_into_es.py" ]   