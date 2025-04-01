import grpc
from concurrent import futures
import time
from datetime import datetime
import os
from google.protobuf.timestamp_pb2 import Timestamp
from google.protobuf.empty_pb2 import Empty
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_

import posts_pb2
import posts_pb2_grpc
from database import engine, Base, SessionLocal
from models import Post, Tag

Base.metadata.create_all(bind=engine)

class PostsServicer(posts_pb2_grpc.PostsServiceServicer):
    def CreatePost(self, request, context):
        db = SessionLocal()
        try:
            post = Post(
                title=request.title,
                description=request.description,
                creator_id=request.creator_id,
                is_private=request.is_private
            )

            for tag_name in request.tags:
                tag = db.query(Tag).filter(Tag.name == tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.add(tag)
                post.tags.append(tag)

            db.add(post)
            db.commit()
            db.refresh(post)

            response = posts_pb2.Post(
                id=post.id,
                title=post.title,
                description=post.description,
                creator_id=post.creator_id,
                is_private=post.is_private
            )

            created_at = Timestamp()
            created_at.FromDatetime(post.created_at)
            response.created_at.CopyFrom(created_at)

            updated_at = Timestamp()
            updated_at.FromDatetime(post.updated_at)
            response.updated_at.CopyFrom(updated_at)

            for tag in post.tags:
                response.tags.append(tag.name)

            return response
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal error: {str(e)}")
            raise
        finally:
            db.close()

    def UpdatePost(self, request, context):
        db = SessionLocal()
        try:
            post = db.query(Post).filter(Post.id == request.id).first()
            if not post:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Post with id {request.id} not found")
                return posts_pb2.Post()

            if post.creator_id != request.creator_id:
                context.set_code(grpc.StatusCode.PERMISSION_DENIED)
                context.set_details("You don't have permission to update this post")
                return posts_pb2.Post()

            post.title = request.title
            post.description = request.description
            post.is_private = request.is_private

            post.tags.clear()
            for tag_name in request.tags:
                tag = db.query(Tag).filter(Tag.name == tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.add(tag)
                post.tags.append(tag)

            db.commit()
            db.refresh(post)

            response = posts_pb2.Post(
                id=post.id,
                title=post.title,
                description=post.description,
                creator_id=post.creator_id,
                is_private=post.is_private
            )

            created_at = Timestamp()
            created_at.FromDatetime(post.created_at)
            response.created_at.CopyFrom(created_at)

            updated_at = Timestamp()
            updated_at.FromDatetime(post.updated_at)
            response.updated_at.CopyFrom(updated_at)

            for tag in post.tags:
                response.tags.append(tag.name)

            return response
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal error: {str(e)}")
            raise
        finally:
            db.close()

    def DeletePost(self, request, context):
        db = SessionLocal()
        try:
            post = db.query(Post).filter(Post.id == request.id).first()
            if not post:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Post with id {request.id} not found")
                return Empty()

            if post.creator_id != request.creator_id:
                context.set_code(grpc.StatusCode.PERMISSION_DENIED)
                context.set_details("You don't have permission to delete this post")
                return Empty()

            db.delete(post)
            db.commit()

            return Empty()
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal error: {str(e)}")
            raise
        finally:
            db.close()

    def GetPost(self, request, context):
        db = SessionLocal()
        try:
            post = db.query(Post).filter(Post.id == request.id).first()
            if not post:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Post with id {request.id} not found")
                return posts_pb2.Post()

            if post.is_private and post.creator_id != request.viewer_id:
                context.set_code(grpc.StatusCode.PERMISSION_DENIED)
                context.set_details("This post is private")
                return posts_pb2.Post()

            response = posts_pb2.Post(
                id=post.id,
                title=post.title,
                description=post.description,
                creator_id=post.creator_id,
                is_private=post.is_private
            )

            created_at = Timestamp()
            created_at.FromDatetime(post.created_at)
            response.created_at.CopyFrom(created_at)

            updated_at = Timestamp()
            updated_at.FromDatetime(post.updated_at)
            response.updated_at.CopyFrom(updated_at)

            for tag in post.tags:
                response.tags.append(tag.name)

            return response
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal error: {str(e)}")
            raise
        finally:
            db.close()

    def ListPosts(self, request, context):
        db = SessionLocal()
        try:
            total_query = db.query(func.count(Post.id)).filter(Post.creator_id == request.creator_id)
            total = total_query.scalar()

            page = max(request.page, 1)
            page_size = min(max(request.page_size, 1), 100)
            offset = (page - 1) * page_size
            total_pages = (total + page_size - 1) // page_size

            posts_query = db.query(Post).filter(Post.creator_id == request.creator_id)
            posts_query = posts_query.order_by(desc(Post.created_at))
            posts_query = posts_query.offset(offset).limit(page_size)
            posts = posts_query.all()

            response = posts_pb2.ListPostsResponse(
                total=total,
                page=page,
                total_pages=total_pages
            )

            for post in posts:
                post_pb = posts_pb2.Post(
                    id=post.id,
                    title=post.title,
                    description=post.description,
                    creator_id=post.creator_id,
                    is_private=post.is_private
                )

                created_at = Timestamp()
                created_at.FromDatetime(post.created_at)
                post_pb.created_at.CopyFrom(created_at)

                updated_at = Timestamp()
                updated_at.FromDatetime(post.updated_at)
                post_pb.updated_at.CopyFrom(updated_at)

                for tag in post.tags:
                    post_pb.tags.append(tag.name)

                response.posts.append(post_pb)

            return response
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal error: {str(e)}")
            raise
        finally:
            db.close()

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    posts_pb2_grpc.add_PostsServiceServicer_to_server(PostsServicer(), server)

    port = os.getenv("PORT", "50051")
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    print(f"Posts service is running on port {port}...")

    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == "__main__":
    serve()
