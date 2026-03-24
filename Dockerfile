FROM python:3.12.8
WORKDIR /app
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]