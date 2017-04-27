import unittest
from mock import patch
from fakeredis import FakeRedis

from saltnanny import SaltRedisClient


class SaltNannyClientTest(unittest.TestCase):

    @patch('redis.Redis')
    def setUp(self, mock_redis):
        self.client = SaltRedisClient('localhost', 6379, '0')
        self.client.redis_instance = FakeRedis()
        self.client.redis_instance.flushall()

    @patch('redis.Redis')
    def test_connection_failure(self, mock_redis):
        mock_redis.side_effect = Exception
        self.assertRaises(Exception, SaltRedisClient, 'localhost', 6379, '0')

    @patch('redis.Redis')
    def test_no_latest_jid(self, mock_redis):
        self.assertEquals('0', self.client.get_latest_jid('minion', 'state.highstate'))

    @patch('redis.Redis')
    def test_get_latest_jid_salt_2015(self, mockRedis):
        self.client.redis_instance.lpush('minion:state.highstate', '1234')
        self.assertEquals('1234', self.client.get_latest_jid('minion', 'state.highstate'))

    @patch('redis.Redis')
    def test_get_latest_jid_salt_2016(self, mockRedis):
        self.client.redis_instance.set('minion:state.highstate', '1234')
        self.assertEquals('1234', self.client.get_latest_jid('minion', 'state.highstate'))

    @patch('redis.Redis')
    def test_get_default_jid(self, mockRedis):
        self.assertEquals('0', self.client.get_latest_jid('minion', 'state.highstate'))

    @patch('redis.Redis')
    def test_get_return_by_jid_salt_2015(self, mockRedis):
        self.client.redis_instance.set('minion:1234', 'Highstate Result')
        self.assertEquals('Highstate Result', self.client.get_return_by_jid('minion', '1234'))

    @patch('redis.Redis')
    def test_get_return_by_jid_salt_2016(self, mockRedis):
        self.client.redis_instance.hset('ret:1234', 'minion', 'Highstate Result')
        self.assertEquals('Highstate Result', self.client.get_return_by_jid('minion', '1234'))

    @patch('redis.Redis')
    def test_get_return_by_jid_nokey(self, mockRedis):
        self.assertRaises(ValueError, self.client.get_return_by_jid, 'minion', '1234')
