import contextlib
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi import Request
from redis import asyncio as aioredis

from app.dependencies.redis import get_connection, get_redis, Redis


@pytest.fixture
def app():
    return FastAPI()


@pytest.fixture
def mock_redis_pool(mocker):
    mock_pool = mocker.AsyncMock(spec=aioredis.Redis)
    mock_client = mocker.AsyncMock()
    mock_conn = mocker.AsyncMock(spec=aioredis.Redis)

    mock_client.__aenter__.return_value = mock_conn
    mock_pool.client.return_value = mock_client

    return mock_pool


@pytest.fixture
def mock_request(app, mock_redis_pool):
    request = Request({"type": "http"})
    request.scope["app"] = app
    request.app.state.redis_pool = mock_redis_pool

    return request


@pytest.fixture
async def mock_redis_instance(mock_request, mock_redis_pool):
    connection_generator = get_connection(mock_request)
    mock_conn = await connection_generator.__anext__()

    return await get_redis(2024, mock_conn)


@pytest.mark.asyncio
async def test_get_connection(mock_request, mock_redis_pool):
    # Act
    connection_generator = get_connection(mock_request)
    connection = await connection_generator.__anext__()

    # Assert
    assert connection == mock_redis_pool.client.return_value.__aenter__.return_value
    mock_redis_pool.client.assert_called_once()

    # Act for StopAsyncIteration
    with contextlib.suppress(StopAsyncIteration):
        await connection_generator.__anext__()

    # Assert
    mock_redis_pool.client.return_value.__aexit__.assert_called_once()


@pytest.mark.asyncio
async def test_get_redis(mock_request, mock_redis_pool):
    # Arrange
    test_year = 2024
    connection_generator = get_connection(mock_request)
    mock_conn = await connection_generator.__anext__()
    redis_instance = await get_redis(test_year, mock_conn)

    assert isinstance(redis_instance, Redis)
    assert redis_instance.year == test_year
    assert redis_instance.connection == mock_conn


@pytest.mark.asyncio
@patch('pickle.loads')
@patch('pickle.dumps')
async def test_redis_instance_get_with_auto_set_method(
        mock_pickle_dumps, mock_pickle_loads, mocker, mock_redis_instance
):
    # case 1: data does not exist
    # Arrange
    mock_redis_instance.connection.get = mocker.AsyncMock(return_value=None)
    mock_redis_instance.connection.set = mocker.AsyncMock()
    mock_func = mocker.AsyncMock(return_value="new_data")
    result = await mock_redis_instance.get_with_auto_set("test_key", mock_func)

    # Assert
    assert result == "new_data"
    mock_func.assert_called_once()
    mock_redis_instance.connection.set.assert_called_once()
    mock_pickle_dumps.assert_called_once_with("new_data")

    # case 2: data exists
    # Arrange
    mock_redis_instance.connection.get.reset_mock()
    mock_redis_instance.connection.set.reset_mock()
    mock_redis_instance.connection.get = mocker.AsyncMock(return_value=b"test_data")

    # Assert
    mock_pickle_loads.called_once_with(b"test_data")
