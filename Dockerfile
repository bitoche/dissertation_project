# import official python-mount
FROM python:alpine

# set up workdir
WORKDIR /app

# copying requirements
COPY requirements.txt .

# installing requirements
RUN pip install --no-cache-dir -r requirements.txt

# copying all code
COPY . .

# set up environment variables
###

# open outer port
EXPOSE 5000

# start app
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]
