import pytest
import grpc
from unittest.mock import MagicMock, patch
from datetime import datetime
import calendar

from server import PostsServicer

@pytest.fixture
def context():
    return MagicMock()

def test_create_post_success(context):
    mock_db = MagicMock()
    request = MagicMock()
    request.title = "Test Post"
    request.description = "Test Description"
    request.creator_id = 1
    request.is_private = False
    request.tags = ["tag1", "tag2"]

    # Mock post and database operations
    post_mock = MagicMock()
    post_mock.id = 1
    post_mock.title = request.title
    post_mock.description = request.description
    post_mock.creator_id = request.creator_id
    post_mock.is_private = request.is_private
    post_mock.created_at = datetime(2025, 1, 1, 12, 0)
    post_mock.updated_at = datetime(2025, 1, 1, 12, 0)
    post_mock.tags = []

    def add_post(p):
        mock_db.add.return_value = None

    mock_db.add.side_effect = add_post
    mock_db.commit.return_value = None

    mock_db.query.return_value.filter.return_value.first.return_value = None

    with patch('server.SessionLocal', return_value=mock_db):
        with patch('server.Post', return_value=post_mock):
            servicer = PostsServicer()
            response = servicer.CreatePost(request, context)

            assert mock_db.add.called
            assert mock_db.commit.called
            assert response.id == 1
            assert response.title == "Test Post"
            assert response.description == "Test Description"

def test_get_post_success(context):
    mock_db = MagicMock()
    request = MagicMock()
    request.id = 1
    request.viewer_id = 1

    post_mock = MagicMock()
    post_mock.id = 1
    post_mock.title = "Test Post"
    post_mock.description = "Test Description"
    post_mock.creator_id = 1
    post_mock.is_private = False
    post_mock.created_at = datetime(2023, 1, 1, 12, 0)
    post_mock.updated_at = datetime(2023, 1, 1, 12, 0)

    tag1 = MagicMock()
    tag1.name = "tag1"
    tag2 = MagicMock()
    tag2.name = "tag2"
    post_mock.tags = [tag1, tag2]

    mock_db.query.return_value.filter.return_value.first.return_value = post_mock

    with patch('server.SessionLocal', return_value=mock_db):
        servicer = PostsServicer()
        response = servicer.GetPost(request, context)

        assert response.id == 1
        assert response.title == "Test Post"
        assert len(response.tags) == 2

def test_private_post_access_denied(context):
    mock_db = MagicMock()
    request = MagicMock()
    request.id = 1
    request.viewer_id = 2

    post_mock = MagicMock()
    post_mock.id = 1
    post_mock.creator_id = 1
    post_mock.is_private = True

    mock_db.query.return_value.filter.return_value.first.return_value = post_mock

    with patch('server.SessionLocal', return_value=mock_db):
        servicer = PostsServicer()
        servicer.GetPost(request, context)

        context.set_code.assert_called_with(grpc.StatusCode.PERMISSION_DENIED)
