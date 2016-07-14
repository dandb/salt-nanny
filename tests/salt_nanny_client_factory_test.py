import unittest
from mock import patch

from saltnanny.salt_nanny_client import SaltNannyClientFactory


class SaltNannyClientFactoryTest(unittest.TestCase):

    @patch('redis.Redis')
    def test_factory(self, mock_redis):
        redis_client = SaltNannyClientFactory.factory('redis', 'localhost', 6379, '0')
        self.assertTrue(redis_client is not None)

    def test_factory_invalid_client(self):
        redis_client = SaltNannyClientFactory.factory('cassandra', 'localhost', 6379, '0')
        self.assertTrue(redis_client is None)
