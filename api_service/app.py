
from fastapi import FastAPI, Request, Response
import httpx
import os

USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user_service:8000")

app = FastAPI()

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy(path: str, request: Request):
    async with httpx.AsyncClient(base_url=USER_SERVICE_URL) as client:
        body = await request.body()
        
        response = await client.request(
            method=request.method,
            url=path,
            headers=dict(request.headers.items()),
            content=body
        )
        
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers)
        )