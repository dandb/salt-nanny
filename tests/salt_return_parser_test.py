import unittest
import os
from mock import patch
from fakeredis import FakeRedis
from saltnanny import SaltReturnParser
from saltnanny import SaltNanny
from saltnanny import SaltRedisClient


class SaltReturnParserTest(unittest.TestCase):

    cache_config = {
        'type': 'redis',
        'host': 'localhost',
        'port': 6379,
        'db': '0'
    }

    @patch('redis.Redis')
    def setUp(self, mock_redis):
        client = SaltRedisClient('localhost', 6379, '0')
        client.redis_instance = FakeRedis()
        self.parser = SaltReturnParser(client)

    def test_process_jids_success(self):
        self.parser.cache_client.redis_instance.set('minion1:1234', '{ "retcode": 0, "result": false }')
        self.parser.cache_client.redis_instance.set('minion2:4321', '{ "retcode": 0, "result": true }')
        result_code = self.parser.process_jids({'minion1':'1234', 'minion2': '4321'}, 2)
        self.assertTrue(result_code > 0)

    def test_process_jids_failure(self):
        self.parser.cache_client.redis_instance.set('minion1:1234', '{ "retcode": 0, "result": true }')
        result_code = self.parser.process_jids({'minion1':'1234'}, 1)
        self.assertTrue(result_code == 0)

    def test_process_jids_failure_invalidresult_random_error(self):
        self.parser.cache_client.redis_instance.set('minion1:1234', '{ "result" : "random stack trace" }')
        result_code = self.parser.process_jids({'minion1':'1234'}, 1)
        self.assertTrue(result_code > 0)

    def test_process_jids_failure_invalidresult(self):
        self.parser.min_interval = 1
        self.parser.max_attempts = 2
        self.parser.cache_client.redis_instance.set('minion1:1234', '{\"return\" : [\"The function state.highstate is running as PID 1234\"]}')
        result_code = self.parser.process_jids({'minion1': '1234'}, 1)
        self.assertTrue(result_code > 0)

    def test_get_return_info(self, ):
        self.parser.min_interval = 1
        self.parser.max_attempts = 2
        self.parser.cache_client.redis_instance.set('minion1:1234', '{\"return\" : [\"The function state.highstate is running as PID 1234\"]}')
        result_code = self.parser.get_return_info('minion1', '1234')
        self.assertTrue(result_code > 0)


    @patch('redis.Redis')
    def test_parse_last_return_with_results(self, mock_redis):
        fake_redis = FakeRedis()

        # Create and initialize Salt Nanny
        salt_nanny = SaltNanny(self.cache_config)
        salt_nanny.cache_client.redis_instance = fake_redis
        salt_nanny.initialize(['minion1'])
        salt_nanny.min_interval = 1

        with open('{0}/resources/failed_highstate.json'.format(os.path.dirname(__file__)), 'r') as f:
            json = f.read()

        # Make Redis Returns available in fake redis
        salt_nanny.cache_client.redis_instance.set('minion1:state.highstate', '6789')
        salt_nanny.cache_client.redis_instance.set('minion1:6789', json)

        return_info = salt_nanny.cache_client.get_return_by_jid('minion1','6789')
        is_failed = self.parser.highstate_failed(return_info)

        self.assertTrue(is_failed)

    def test_process_jids_noresults(self):
        result_code = self.parser.process_jids({}, 1)
        self.assertTrue(result_code == 2)

    def test_process_jids_partial(self):
        self.parser.cache_client.redis_instance.set('minion1:1234', '{ "retcode": 0, "result": true }')
        result_code = self.parser.process_jids({'minion1': '1234'}, 2)
        self.assertTrue(result_code == 1)

    def test_check_custom_event_failure_failure(self):
        self.parser.cache_client.redis_instance.set('custom_event', '\"Custom String Return with Failure\"')
        result_code = self.parser.check_custom_event_failure('custom_event', 'Failure', '')
        self.assertTrue(result_code > 0)

    def test_check_custom_event_failure_failure_forlist(self):
        self.parser.cache_client.redis_instance.set('custom_event', '[\"Custom String Return with Failure\"]')
        result_code = self.parser.check_custom_event_failure('custom_event', 'Failure', '')
        self.assertTrue(result_code > 0)

    def test_check_custom_event_failure_success(self):
        self.parser.cache_client.redis_instance.set('custom_event', '\"Happy with a success.\"')
        result_code = self.parser.check_custom_event_failure('custom_event', '', 'success')
        self.assertTrue(result_code == 0)


    def test_check_custom_event_failure_success_forlist(self):
        self.parser.cache_client.redis_instance.set('custom_event', '[\"Happy with a success.\"]')
        result_code = self.parser.check_custom_event_failure('custom_event', '', 'success')
        self.assertTrue(result_code == 0)
