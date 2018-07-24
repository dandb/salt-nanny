import os
import pytest
import mock
from mock import MagicMock
from mock import call
from fakeredis import FakeRedis

from saltnanny import SaltNanny


@pytest.fixture(autouse=True)
def cache_config():
    yield {
        'type': 'redis',
        'host': 'localhost',
        'port': 6379,
        'db': '0'
    }


@pytest.fixture(autouse=True)
def salt_nanny(cache_config):
    with mock.patch('redis.Redis'):
        salt_nanny = SaltNanny(cache_config)

    salt_nanny.cache_client.redis_instance = FakeRedis()
    salt_nanny.min_interval = 1

    yield salt_nanny


def test_initialize(salt_nanny):
    salt_nanny.cache_client = MagicMock()
    salt_nanny.initialize(['minion1', 'minion2'])
    salt_nanny.cache_client.get_latest_jid.assert_has_calls([call('minion1', 'state.highstate'), call('minion2', 'state.highstate')])


def test_initialize_nominions(salt_nanny):
    salt_nanny.cache_client = MagicMock()

    with pytest.raises(ValueError):
        salt_nanny.initialize([])


# def test_track_returns_minion_2(salt_nanny):
#     fake_redis = salt_nanny.cache_client.redis_instance
#     fake_redis.set('minion1:state.highstate', '1234')
#
#     salt_nanny.initialize(['minion1'])
#
#     # Make Redis Returns available in fake redis
#     fake_redis.set('minion1:state.highstate', '4321')
#     fake_redis.hset('ret:4321', 'minion1', 'Highstate Result1')
#     fake_redis.hset('ret:1234', 'minion2', 'Highstate Result1')
#
#     # Start tracking returns
#     assert salt_nanny.track_returns(2) == 0


def test_track_returns_no_pending_minion_list(salt_nanny):
    fake_redis = salt_nanny.cache_client.redis_instance
    fake_redis.set('minion1:state.highstate', '1234')
    fake_redis.set('minion2:state.highstate', '1234')

    salt_nanny.initialize(['minion1', 'minion2'])
    salt_nanny.completed_minions = {'minion1': 'completed 1'}

    # Make Redis Returns available in fake redis
    fake_redis.set('minion2:state.highstate', '4321')
    fake_redis.hset('ret:1234', 'minion1', 'Highstate Result1')
    fake_redis.hset('ret:4321', 'minion2', 'Highstate Result1')

    # Start tracking returns
    assert salt_nanny.track_returns(2) == 0


def test_track_returns_no_match(salt_nanny):
    fake_redis = salt_nanny.cache_client.redis_instance
    fake_redis.set('minion1:state.highstate', '1234')

    salt_nanny.initialize(['minion1', 'minion2'])

    # Make Redis Returns available in fake redis
    fake_redis.set('minion2:state.highstate', '4321')
    fake_redis.hset('ret:1234', 'minion1', 'Highstate Result1')
    fake_redis.hset('ret:1234', 'minion2', 'Highstate Result1')

    # Start tracking returns
    assert 2 == salt_nanny.track_returns(2)


def test_track_returns(salt_nanny):
    salt_nanny.initialize(['minion1', 'minion2'])

    # Make Redis Returns available in fake redis
    fake_redis = salt_nanny.cache_client.redis_instance
    fake_redis.set('minion1:state.highstate', '1234')
    fake_redis.set('minion2:state.highstate', '4321')
    fake_redis.hset('ret:1234', 'minion1', 'Highstate Result1')
    fake_redis.hset('ret:1234', 'minion2', 'Highstate Result1')

    # Start tracking returns
    salt_nanny.track_returns(1)


def test_parse_last_return(salt_nanny):
    salt_nanny.initialize(['minion1'])

    with open('{0}/resources/highstate.json'.format(os.path.dirname(__file__)), 'r') as f:
        json = f.read()

    # Make Redis Returns available in fake redis
    fake_redis = salt_nanny.cache_client.redis_instance
    fake_redis.set('minion1:state.highstate', '6789')
    fake_redis.set('minion1:6789', json)

    assert salt_nanny.parse_last_return() > 0


def test_parse_last_return_with_results(salt_nanny):
    salt_nanny.initialize(['minion1'])

    with open('{0}/resources/highstate.json'.format(os.path.dirname(__file__)), 'r') as f:
        json = f.read()

    # Make Redis Returns available in fake redis
    fake_redis = salt_nanny.cache_client.redis_instance
    fake_redis.set('minion1:state.highstate', '6789')
    fake_redis.set('minion1:6789', json)

    # 6789 is higher than JID 6666 so the json will be fetched
    assert salt_nanny.parse_last_return(6666) == 2


def test_parse_last_return_with_no_results(salt_nanny):
    salt_nanny.initialize(['minion1'])

    with open('{0}/resources/highstate.json'.format(os.path.dirname(__file__)), 'r') as f:
        json = f.read()

    # Make Redis Returns available in fake redis
    fake_redis = salt_nanny.cache_client.redis_instance
    fake_redis.set('minion1:state.highstate', '6789')
    fake_redis.set('minion1:6789', json)

    # 6789 is lower than JID 7777 so no results expected
    assert salt_nanny.parse_last_return(7777) == 1


def test_track_custom_event_failures_no_failures(salt_nanny):
    fake_redis = salt_nanny.cache_client.redis_instance
    fake_redis.set('custom_event_type', '["Random Event Log", "Success"]')
    return_code = salt_nanny.track_custom_event_failures('custom_event_type', ['Failure'], 2)
    assert return_code == 0


def test_track_custom_event_failures(salt_nanny):
    fake_redis = salt_nanny.cache_client.redis_instance
    fake_redis.set('custom_event_type', '["Random Event Log", "Failure"]')
    return_code = salt_nanny.track_custom_event_failures('custom_event_type', ['Failure'], 2)

    assert return_code > 0


def test_track_custom_event_failures_key_not_found(salt_nanny):
    fake_redis = salt_nanny.cache_client.redis_instance
    fake_redis.set('custom_event_type', '["Random Event Log", "Failure"]')
    return_code = salt_nanny.track_custom_event_failures('event_no_match', ['Failure'], 1)

    assert return_code == 1


def test_get_wait_time(cache_config):
    with mock.patch('redis.Redis'):
        salt_nanny = SaltNanny(cache_config, 'test')
    assert salt_nanny.get_wait_time(0) == 15
    assert salt_nanny.get_wait_time(1) == 30
    assert salt_nanny.get_wait_time(2) == 60
    assert salt_nanny.get_wait_time(3) == 60


def test_setup_logging(cache_config):
    with mock.patch('redis.Redis'):
        salt_nanny = SaltNanny(cache_config, 'test')

    assert salt_nanny.log is not None

@mock.patch('os.makedirs')
@mock.patch('os.path.exists')
def test_setup_logging_make_logfile(mock_exists, mock_makedirs, cache_config):
    mock_exists.return_value = False
    mock_makedirs.return_value = False
    with mock.patch('redis.Redis'):
        salt_nanny = SaltNanny(cache_config, 'missing_log_dir')

    assert salt_nanny.log is not None
    mock_exists.assert_called_once_with(os.path.join(os.getcwd(), 'logs'))
