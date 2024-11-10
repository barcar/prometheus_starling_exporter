FROM python:slim
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY app.py .
EXPOSE 9822
CMD ["python3", "app.py"]
