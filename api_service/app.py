import os
import grpc
import httpx
from fastapi import FastAPI, Request, Response, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from auth import get_current_user
import posts_pb2
import posts_pb2_grpc

app = FastAPI()

USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user_service:8000")
POST_SERVICE_URL = os.getenv("POST_SERVICE_URL", "post_service:50051")

class PostCreateModel(BaseModel):
    title: str
    description: str
    is_private: bool = False
    tags: List[str] = []

class PostUpdateModel(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_private: Optional[bool] = None
    tags: Optional[List[str]] = None

class PostResponseModel(BaseModel):
    id: int
    title: str
    description: str
    creator_id: int
    created_at: datetime
    updated_at: datetime
    is_private: bool
    tags: List[str] = []

class PaginatedPostsResponse(BaseModel):
    posts: List[PostResponseModel]
    total: int
    page: int
    total_pages: int

@app.api_route("/register", methods=["POST"])
async def proxy_register(request: Request):
    return await proxy_to_user_service(request)

@app.api_route("/login", methods=["POST"])
async def proxy_login(request: Request):
    return await proxy_to_user_service(request)

@app.api_route("/users/me", methods=["GET", "PUT"])
async def proxy_users_me(request: Request):
    return await proxy_to_user_service(request)

async def proxy_to_user_service(request: Request):
    body = await request.body()
    async with httpx.AsyncClient(base_url=USER_SERVICE_URL) as client:
        response = await client.request(
            method=request.method,
            url=request.url.path,
            headers=dict(request.headers.items()),
            content=body
        )
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers)
        )

@app.post("/posts", response_model=PostResponseModel, status_code=201)
async def create_post(post: PostCreateModel, current_user: dict = Depends(get_current_user)):
    try:
        with grpc.insecure_channel(POST_SERVICE_URL) as channel:
            stub = posts_pb2_grpc.PostsServiceStub(channel)

            request = posts_pb2.CreatePostRequest(
                title=post.title,
                description=post.description,
                creator_id=current_user["id"],
                is_private=post.is_private,
                tags=post.tags
            )

            response = stub.CreatePost(request)

            return {
                "id": response.id,
                "title": response.title,
                "description": response.description,
                "creator_id": response.creator_id,
                "created_at": response.created_at.ToDatetime(),
                "updated_at": response.updated_at.ToDatetime(),
                "is_private": response.is_private,
                "tags": list(response.tags)
            }
    except grpc.RpcError as e:
        status_code = e.code()
        if status_code == grpc.StatusCode.INTERNAL:
            raise HTTPException(status_code=500, detail="Internal server error")
        elif status_code == grpc.StatusCode.PERMISSION_DENIED:
            raise HTTPException(status_code=403, detail=e.details())
        elif status_code == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(status_code=404, detail=e.details())
        else:
            raise HTTPException(status_code=500, detail=f"gRPC error: {e.details()}")

@app.get("/posts/{post_id}", response_model=PostResponseModel)
async def get_post(post_id: int, current_user: dict = Depends(get_current_user)):
    try:
        with grpc.insecure_channel(POST_SERVICE_URL) as channel:
            stub = posts_pb2_grpc.PostsServiceStub(channel)

            request = posts_pb2.GetPostRequest(
                id=post_id,
                viewer_id=current_user["id"]
            )

            response = stub.GetPost(request)

            return {
                "id": response.id,
                "title": response.title,
                "description": response.description,
                "creator_id": response.creator_id,
                "created_at": response.created_at.ToDatetime(),
                "updated_at": response.updated_at.ToDatetime(),
                "is_private": response.is_private,
                "tags": list(response.tags)
            }
    except grpc.RpcError as e:
        status_code = e.code()
        if status_code == grpc.StatusCode.INTERNAL:
            raise HTTPException(status_code=500, detail="Internal server error")
        elif status_code == grpc.StatusCode.PERMISSION_DENIED:
            raise HTTPException(status_code=403, detail=e.details())
        elif status_code == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(status_code=404, detail=e.details())
        else:
            raise HTTPException(status_code=500, detail=f"gRPC error: {e.details()}")

@app.put("/posts/{post_id}", response_model=PostResponseModel)
async def update_post(post_id: int, post: PostUpdateModel, current_user: dict = Depends(get_current_user)):
    try:
        with grpc.insecure_channel(POST_SERVICE_URL) as channel:
            stub = posts_pb2_grpc.PostsServiceStub(channel)

            get_request = posts_pb2.GetPostRequest(
                id=post_id,
                viewer_id=current_user["id"]
            )

            try:
                current_post = stub.GetPost(get_request)
            except grpc.RpcError as e:
                if e.code() == grpc.StatusCode.NOT_FOUND:
                    raise HTTPException(status_code=404, detail="Post not found")
                elif e.code() == grpc.StatusCode.PERMISSION_DENIED:
                    raise HTTPException(status_code=403, detail=e.details())
                else:
                    raise

            if current_post.creator_id != current_user["id"]:
                raise HTTPException(status_code=403, detail="You don't have permission to update this post")

            title = post.title if post.title is not None else current_post.title
            description = post.description if post.description is not None else current_post.description
            is_private = post.is_private if post.is_private is not None else current_post.is_private
            tags = post.tags if post.tags is not None else list(current_post.tags)

            update_request = posts_pb2.UpdatePostRequest(
                id=post_id,
                creator_id=current_user["id"],
                title=title,
                description=description,
                is_private=is_private,
                tags=tags
            )

            response = stub.UpdatePost(update_request)

            return {
                "id": response.id,
                "title": response.title,
                "description": response.description,
                "creator_id": response.creator_id,
                "created_at": response.created_at.ToDatetime(),
                "updated_at": response.updated_at.ToDatetime(),
                "is_private": response.is_private,
                "tags": list(response.tags)
            }
    except grpc.RpcError as e:
        status_code = e.code()
        if status_code == grpc.StatusCode.INTERNAL:
            raise HTTPException(status_code=500, detail="Internal server error")
        else:
            raise HTTPException(status_code=500, detail=f"gRPC error: {e.details()}")

@app.delete("/posts/{post_id}", status_code=204)
async def delete_post(post_id: int, current_user: dict = Depends(get_current_user)):
    try:
        with grpc.insecure_channel(POST_SERVICE_URL) as channel:
            stub = posts_pb2_grpc.PostsServiceStub(channel)

            request = posts_pb2.DeletePostRequest(
                id=post_id,
                creator_id=current_user["id"]
            )

            stub.DeletePost(request)

            return Response(status_code=204)
    except grpc.RpcError as e:
        status_code = e.code()
        if status_code == grpc.StatusCode.INTERNAL:
            raise HTTPException(status_code=500, detail="Internal server error")
        elif status_code == grpc.StatusCode.PERMISSION_DENIED:
            raise HTTPException(status_code=403, detail=e.details())
        elif status_code == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(status_code=404, detail=e.details())
        else:
            raise HTTPException(status_code=500, detail=f"gRPC error: {e.details()}")

@app.get("/posts", response_model=PaginatedPostsResponse)
async def list_posts(page: int = 1, page_size: int = 10, current_user: dict = Depends(get_current_user)):
    try:
        with grpc.insecure_channel(POST_SERVICE_URL) as channel:
            stub = posts_pb2_grpc.PostsServiceStub(channel)

            request = posts_pb2.ListPostsRequest(
                creator_id=current_user["id"],
                page=page,
                page_size=page_size
            )

            response = stub.ListPosts(request)

            posts = []
            for post in response.posts:
                posts.append({
                    "id": post.id,
                    "title": post.title,
                    "description": post.description,
                    "creator_id": post.creator_id,
                    "created_at": post.created_at.ToDatetime(),
                    "updated_at": post.updated_at.ToDatetime(),
                    "is_private": post.is_private,
                    "tags": list(post.tags)
                })

            return {
                "posts": posts,
                "total": response.total,
                "page": response.page,
                "total_pages": response.total_pages
            }
    except grpc.RpcError as e:
        status_code = e.code()
        if status_code == grpc.StatusCode.INTERNAL:
            raise HTTPException(status_code=500, detail="Internal server error")
        else:
            raise HTTPException(status_code=500, detail=f"gRPC error: {e.details()}")
