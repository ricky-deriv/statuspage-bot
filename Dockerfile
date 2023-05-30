FROM python:3.11.3-slim-bullseye

WORKDIR /lib

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-u", "./lib/app.py"]