import pytest
import mock
from fakeredis import FakeRedis
from saltnanny import SaltRedisClient


@pytest.fixture(autouse=True)
def nanny_client():
    with mock.patch('redis.Redis'):
        client = SaltRedisClient('localhost', 6379, '0')
        client.redis_instance = FakeRedis()
        client.redis_instance.flushall()
        yield client


@mock.patch('redis.Redis')
def test_connection_failure(mock_redis):
    mock_redis.side_effect = Exception

    with pytest.raises(Exception):
        SaltRedisClient('localhost', 6379, '0')


def test_no_latest_jid(nanny_client):
    assert nanny_client.get_latest_jid('minion', 'state.highstate') == '0'


def test_get_latest_jid_salt_2015(nanny_client):
    nanny_client.redis_instance.lpush('minion:state.highstate', '1234')
    assert nanny_client.get_latest_jid('minion', 'state.highstate') == '1234'


def test_get_latest_jid_salt_2016(nanny_client):
    nanny_client.redis_instance.set('minion:state.highstate', '1234')
    assert nanny_client.get_latest_jid('minion', 'state.highstate') == '1234'


def test_get_latest_jid_default_jid(nanny_client):
    assert nanny_client.get_latest_jid('minion', 'state.highstate') == '0'


def test_get_latest_jid_default_jid_with_key_error(nanny_client):
    with mock.patch.object(nanny_client.redis_instance, 'type', side_effect=KeyError('my test error')):
        assert nanny_client.get_latest_jid('minion', 'state.highstate') == '0'


def test_get_return_by_jid_salt_2015(nanny_client):
    nanny_client.redis_instance.set('minion:1234', 'Highstate Result')
    assert nanny_client.get_return_by_jid('minion', '1234') == 'Highstate Result'


def test_get_return_by_jid_salt_2016(nanny_client):
    nanny_client.redis_instance.hset('ret:1234', 'minion', 'Highstate Result')
    assert nanny_client.get_return_by_jid('minion', '1234') == 'Highstate Result'


def test_get_return_by_jid_nokey(nanny_client):
    with pytest.raises(Exception):
        nanny_client.get_return_by_jid('minion', '1234')
