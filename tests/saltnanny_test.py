import unittest
from mock import MagicMock
from mock import call
from mock import patch
from fakeredis import FakeRedis

from saltnanny import SaltNanny


class SaltNannyTest(unittest.TestCase):

    cache_config = {
        'type': 'redis',
        'host': 'localhost',
        'port': 6379,
        'db': '0'
    }

    @patch('redis.Redis')
    def test_initialize(self, mock_redis):
        salt_nanny = SaltNanny(self.cache_config)
        salt_nanny.cache_client = MagicMock()
        salt_nanny.initialize(['minion1', 'minion2'])
        salt_nanny.cache_client.get_latest_jid.assert_has_calls([call('minion1', 'state.highstate'), call('minion2', 'state.highstate')])

    @patch('redis.Redis')
    def test_initialize_nominions(self, mock_redis):
        salt_nanny = SaltNanny(self.cache_config)
        salt_nanny.cache_client = MagicMock()
        self.assertRaises(ValueError, salt_nanny.initialize, [])

    @patch('redis.Redis')
    def test_track_returns(self, mock_redis):
        fake_redis = FakeRedis()

        # Create and initialize Salt Nanny
        salt_nanny = SaltNanny(self.cache_config)
        salt_nanny.cache_client.redis_instance = fake_redis
        salt_nanny.initialize(['minion1', 'minion2'])
        salt_nanny.min_interval = 1

        # Make Redis Returns available in fake redis
        fake_redis.set('minion1:state.highstate', '1234')
        fake_redis.set('minion2:state.highstate', '4321')
        fake_redis.hset('ret:1234', 'minion1', 'Highstate Result1')
        fake_redis.hset('ret:1234', 'minion2', 'Highstate Result1')

        # Start tracking returns
        salt_nanny.track_returns()

    @patch('redis.Redis')
    def test_get_wait_time(self, mock_redis):
        cache_client = MagicMock()
        salt_nanny = SaltNanny(self.cache_config)
        self.assertEquals(15, salt_nanny.get_wait_time(0))
        self.assertEquals(30, salt_nanny.get_wait_time(1))
        self.assertEquals(60, salt_nanny.get_wait_time(2))
        self.assertEquals(60, salt_nanny.get_wait_time(3))

    @patch('redis.Redis')
    def test_setup_logging(self, mock_redis):
        salt_nanny = SaltNanny(self.cache_config)
        self.assertTrue(salt_nanny.log is not None)
