import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app import app

client = TestClient(app)

@patch('httpx.AsyncClient.request')
def test_proxy_forwards_request(mock_request):
    mock_response = MagicMock()
    mock_response.content = b'{"message": "Success"}'
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "application/json"}
    mock_request.return_value = mock_response
    
    response = client.get("/test-endpoint")
    
    mock_request.assert_called_once()
    assert response.status_code == 200
    assert response.json() == {"message": "Success"}