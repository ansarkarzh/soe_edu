FROM python:3.9

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p protos

COPY protos/*.proto protos/

RUN python -m grpc_tools.protoc -I./protos --python_out=. --grpc_python_out=. ./protos/posts.proto

CMD ["python", "server.py"]
