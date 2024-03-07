FROM python:3.11

WORKDIR /app

COPY . . 

RUN pip install -r requirements.txt
RUN pip install HAP-python[QRCode]

CMD ["python", "homekit.py"]