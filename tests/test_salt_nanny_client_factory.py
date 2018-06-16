import mock
from saltnanny import SaltNannyClientFactory


def test_factory():
    with mock.patch('redis.Redis'):
        redis_client = SaltNannyClientFactory.factory('redis', 'localhost', 6379, '0')
    assert redis_client is not None


def test_factory_invalid_client():
    redis_client = SaltNannyClientFactory.factory('cassandra', 'localhost', 6379, '0')
    assert redis_client is None
