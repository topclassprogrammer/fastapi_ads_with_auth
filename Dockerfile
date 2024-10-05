FROM python:3.12.3-bookworm
RUN apt-get update && apt-get install -y libpq-dev gcc python3-dev --no-install-recommends
RUN pip install --upgrade pip
COPY /requirements.txt /requirements.txt
RUN pip install -r /requirements.txt
COPY /app /app
WORKDIR /app
ENTRYPOINT ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
