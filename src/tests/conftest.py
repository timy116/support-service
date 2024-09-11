from .fixtures import *


@pytest.fixture
def anyio_backend():
    return 'asyncio'
