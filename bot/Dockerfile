FROM python:3.12-alpine

WORKDIR /usr/src/bot

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV LOGS_FOLDER="logs/"

CMD ["python", "main.py"]
