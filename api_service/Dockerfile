FROM python:3.9

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY protos/ ./protos/

RUN python -m grpc_tools.protoc -I./protos --python_out=. --grpc_python_out=. ./protos/posts.proto

COPY . .

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
