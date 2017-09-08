import os
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
    def test_parse_last_return(self, mock_redis):
        fake_redis = FakeRedis()

        # Create and initialize Salt Nanny
        salt_nanny = SaltNanny(self.cache_config)
        salt_nanny.cache_client.redis_instance = fake_redis
        salt_nanny.initialize(['minion1'])
        salt_nanny.min_interval = 1

        with open('{0}/resources/highstate.json'.format(os.path.dirname(__file__)), 'r') as f:
            json = f.read()

        # Make Redis Returns available in fake redis
        fake_redis.set('minion1:state.highstate', '6789')
        fake_redis.set('minion1:6789', json)

        self.assertTrue(salt_nanny.parse_last_return() > 0)

    @patch('redis.Redis')
    def test_parse_last_return_with_results(self, mock_redis):
        fake_redis = FakeRedis()

        # Create and initialize Salt Nanny
        salt_nanny = SaltNanny(self.cache_config)
        salt_nanny.cache_client.redis_instance = fake_redis
        salt_nanny.initialize(['minion1'])
        salt_nanny.min_interval = 1

        with open('{0}/resources/highstate.json'.format(os.path.dirname(__file__)), 'r') as f:
            json = f.read()

        # Make Redis Returns available in fake redis
        fake_redis.set('minion1:state.highstate', '6789')
        fake_redis.set('minion1:6789', json)

        # 6789 is higher than JID 6666 so the json will be fetched
        self.assertTrue(salt_nanny.parse_last_return(6666) == 2)

    @patch('redis.Redis')
    def test_parse_last_return_with_no_results(self, mock_redis):
        fake_redis = FakeRedis()

        # Create and initialize Salt Nanny
        salt_nanny = SaltNanny(self.cache_config)
        salt_nanny.cache_client.redis_instance = fake_redis
        salt_nanny.initialize(['minion1'])
        salt_nanny.min_interval = 1

        with open('{0}/resources/highstate.json'.format(os.path.dirname(__file__)), 'r') as f:
            json = f.read()

        # Make Redis Returns available in fake redis
        fake_redis.set('minion1:state.highstate', '6789')
        fake_redis.set('minion1:6789', json)

        # 6789 is lower than JID 7777 so no results expected
        self.assertTrue(salt_nanny.parse_last_return(7777) == 1)

    @patch('redis.Redis')
    def test_track_custom_event_failures_no_failures(self, mock_redis):
        fake_redis = FakeRedis()
        fake_redis.set('custom_event_type', '["Random Event Log", "Success"]')
        # Create and initialize Salt Nanny
        salt_nanny = SaltNanny(self.cache_config)
        salt_nanny.cache_client.redis_instance = fake_redis
        salt_nanny.min_interval = 1
        return_code = salt_nanny.track_custom_event_failures('custom_event_type', ['Failure'], 2)
        self.assertTrue(return_code == 0)

    @patch('redis.Redis')
    def test_track_custom_event_failures(self, mock_redis):
        fake_redis = FakeRedis()
        fake_redis.set('custom_event_type', '["Random Event Log", "Failure"]')
        # Create and initialize Salt Nanny
        salt_nanny = SaltNanny(self.cache_config)
        salt_nanny.cache_client.redis_instance = fake_redis
        salt_nanny.min_interval = 1
        return_code = salt_nanny.track_custom_event_failures('custom_event_type', ['Failure'], 2)
        self.assertTrue(return_code > 0)

    @patch('redis.Redis')
    def test_get_wait_time(self, mock_redis):
        salt_nanny = SaltNanny(self.cache_config)
        self.assertEquals(15, salt_nanny.get_wait_time(0))
        self.assertEquals(30, salt_nanny.get_wait_time(1))
        self.assertEquals(60, salt_nanny.get_wait_time(2))
        self.assertEquals(60, salt_nanny.get_wait_time(3))

    @patch('redis.Redis')
    def test_setup_logging(self, mock_redis):
        salt_nanny = SaltNanny(self.cache_config, 'test')
        self.assertTrue(salt_nanny.log is not None)
