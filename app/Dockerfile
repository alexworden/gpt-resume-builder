FROM python:3.10

RUN mkdir /app
WORKDIR /app
ADD . /app/
RUN pip install -r requirements.txt

EXPOSE 8000
CMD ["python", "/app/APIServer.py"]
