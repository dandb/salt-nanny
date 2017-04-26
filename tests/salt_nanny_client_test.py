import unittest
from mock import patch
from fakeredis import FakeRedis

from saltnanny import SaltRedisClient


class SaltNannyClientTest(unittest.TestCase):

    def setup_client(self):
        client = SaltRedisClient('localhost', 6379, '0')
        client.redis_instance = FakeRedis()
        client.redis_instance.flushall()
        return client

    @patch('redis.Redis')
    def test_connection_failure(self, mock_redis):
        mock_redis.side_effect = Exception
        self.assertRaises(Exception, SaltRedisClient, 'localhost', 6379, '0')

    @patch('redis.Redis')
    def test_no_latest_jid_default_zero(self, mock_redis):
        client = self.setup_client()
        self.assertEquals('0', client.get_latest_jid('minion', 'state.highstate'))

    @patch('redis.Redis')
    def test_get_latest_jid_salt_2015(self, mockRedis):
        client = self.setup_client()
        client.redis_instance.lpush('minion:state.highstate', '1234')
        self.assertEquals('1234', client.get_latest_jid('minion', 'state.highstate'))

    @patch('redis.Redis')
    def test_get_latest_jid_salt_2016(self, mockRedis):
        client = self.setup_client()
        client.redis_instance.set('minion:state.highstate', '1234')
        self.assertEquals('1234', client.get_latest_jid('minion', 'state.highstate'))

    @patch('redis.Redis')
    def test_get_default_jid(self, mockRedis):
        client = self.setup_client()
        self.assertEquals('0', client.get_latest_jid('minion', 'state.highstate'))

    @patch('redis.Redis')
    def test_get_return_by_jid_salt_2015(self, mockRedis):
        client = self.setup_client()
        client.redis_instance.set('minion:1234', 'Highstate Result')
        self.assertEquals('Highstate Result', client.get_return_by_jid('minion', '1234'))

    @patch('redis.Redis')
    def test_get_return_by_jid_salt_2016(self, mockRedis):
        client = self.setup_client()
        client.redis_instance.hset('ret:1234', 'minion', 'Highstate Result')
        self.assertEquals('Highstate Result', client.get_return_by_jid('minion', '1234'))

    @patch('redis.Redis')
    def test_get_return_by_jid_nokey(self, mockRedis):
        client = self.setup_client()
        self.assertRaises(ValueError, client.get_return_by_jid, 'minion', '1234')
