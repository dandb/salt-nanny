import unittest
from mock import patch
from fakeredis import FakeRedis

from saltnanny import SaltReturnParser
from saltnanny import SaltRedisClient


class SaltReturnParserTest(unittest.TestCase):

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

    def test_process_jids_failure_invalidresult(self):
        self.parser.cache_client.redis_instance.set('minion1:1234', '{ "result" : "random stack trace" }')
        result_code = self.parser.process_jids({'minion1':'1234'}, 1)
        self.assertTrue(result_code > 0)

    def test_process_jids_failure_invalidresult(self):
        self.parser.min_interval=1
        self.parser.max_attempts=2
        self.parser.cache_client.redis_instance.set('minion1:1234', '{\"return\" : \"The function state.highstate is running as PID 1234\"}')
        result_code = self.parser.process_jids({'minion1':'1234'}, 1)
        self.assertTrue(result_code > 0)

    def test_process_jids_noresults(self):
        result_code = self.parser.process_jids({}, 1)
        self.assertTrue(result_code == 2)

    def test_process_jids_partial(self):
        self.parser.cache_client.redis_instance.set('minion1:1234', '{ "retcode": 0, "result": true }')
        result_code = self.parser.process_jids({'minion1': '1234'}, 2)
        self.assertTrue(result_code == 1)
