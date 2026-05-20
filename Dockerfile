FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# The trailing slash tells Docker to copy the CONTENTS of the folder, not the folder itself
COPY ./app/ .

# We also remove --reload because we don't want dev-reloaders running in production
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
