import pytest
import mock
import os

from fakeredis import FakeRedis
from saltnanny import SaltReturnParser, SaltNanny, SaltRedisClient


@pytest.fixture(autouse=True)
def salt_return_parser():
    with mock.patch('redis.Redis'):
        client = SaltRedisClient('localhost', 6379, '0')
        client.redis_instance = FakeRedis()
        yield SaltReturnParser(client)


def test_process_jids_success(salt_return_parser):
    salt_return_parser.cache_client.redis_instance.set('minion1:1234', '{ "retcode": 0, "result": false }')
    salt_return_parser.cache_client.redis_instance.set('minion2:4321', '{ "retcode": 0, "result": true }')
    result_code = salt_return_parser.process_jids({'minion1': '1234', 'minion2': '4321'}, 2)
    assert result_code > 0


def test_process_jids_failure(salt_return_parser):
    salt_return_parser.cache_client.redis_instance.set('minion1:1234', '{ "retcode": 0, "result": true }')
    result_code = salt_return_parser.process_jids({'minion1': '1234'}, 1)
    assert result_code == 0


def test_process_jids_failure_invalidresult_random_error(salt_return_parser):
    salt_return_parser.cache_client.redis_instance.set('minion1:1234', '{ "result" : "random stack trace" }')
    result_code = salt_return_parser.process_jids({'minion1':'1234'}, 1)
    assert result_code > 0


def test_process_jids_failure_invalidresult(salt_return_parser):
    salt_return_parser.min_interval = 1
    salt_return_parser.max_attempts = 2
    salt_return_parser.cache_client.redis_instance.set('minion1:1234', '{\"return\" : [\"The function state.highstate is running as PID 1234\"]}')
    result_code = salt_return_parser.process_jids({'minion1': '1234'}, 1)
    assert result_code > 0


def test_get_return_info(salt_return_parser):
    salt_return_parser.min_interval = 1
    salt_return_parser.max_attempts = 2
    salt_return_parser.cache_client.redis_instance.set('minion1:1234', '{\"return\" : [\"The function state.highstate is running as PID 1234\"]}')
    return_dict, return_code = salt_return_parser.get_return_info('minion1', '1234')
    assert return_code > 0


def test_parse_last_return_with_results(salt_return_parser):
    with mock.patch('redis.Redis'):
        # Create and initialize Salt Nanny
        cache_config = {
            'type': 'redis',
            'host': 'localhost',
            'port': 6379,
            'db': '0'
        }

        salt_nanny = SaltNanny(cache_config)
        salt_nanny.cache_client.redis_instance = FakeRedis()
        salt_nanny.initialize(['minion1'])
        salt_nanny.min_interval = 1

        with open('{0}/resources/failed_highstate.json'.format(os.path.dirname(__file__)), 'r') as f:
            json = f.read()

        # Make Redis Returns available in fake redis
        salt_nanny.cache_client.redis_instance.set('minion1:state.highstate', '6789')
        salt_nanny.cache_client.redis_instance.set('minion1:6789', json)

        return_info = salt_nanny.cache_client.get_return_by_jid('minion1', '6789')
        is_failed = salt_return_parser.highstate_failed(return_info)

    assert is_failed is True


def test_process_jids_noresults(salt_return_parser):
    result_code = salt_return_parser.process_jids({}, 1)
    assert result_code == 2


def test_process_jids_partial(salt_return_parser):
    salt_return_parser.cache_client.redis_instance.set('minion1:1234', '{ "retcode": 0, "result": true }')
    result_code = salt_return_parser.process_jids({'minion1': '1234'}, 2)
    assert result_code == 1


def test_check_custom_event_failure_failure2(salt_return_parser):
    salt_return_parser.cache_client.redis_instance.set('custom_event', '\"Custom String Return no match\"')
    result_code = salt_return_parser.check_custom_event_failure('custom_event', '', '')
    assert result_code == 0


def test_check_custom_event_failure_failure(salt_return_parser):
    salt_return_parser.cache_client.redis_instance.set('custom_event', '\"Custom String Return with Failure\"')
    result_code = salt_return_parser.check_custom_event_failure('custom_event', 'Failure', '')
    assert result_code > 0


def test_check_custom_event_failure_failure_forlist(salt_return_parser):
    salt_return_parser.cache_client.redis_instance.set('custom_event', '[\"Custom String Return with Failure\"]')
    result_code = salt_return_parser.check_custom_event_failure('custom_event', 'Failure', '')
    assert result_code > 0


def test_check_custom_event_failure_success(salt_return_parser):
    salt_return_parser.cache_client.redis_instance.set('custom_event', '\"Happy with a success.\"')
    result_code = salt_return_parser.check_custom_event_failure('custom_event', '', 'success')
    assert result_code == 0


def test_check_custom_event_failure_success_forlist(salt_return_parser):
    salt_return_parser.cache_client.redis_instance.set('custom_event', '[\"Happy with a success.\"]')
    result_code = salt_return_parser.check_custom_event_failure('custom_event', '', 'success')
    assert result_code == 0


def test_is_fun_running_true(salt_return_parser):
    assert salt_return_parser.is_fun_running({'return': ['is running as PID test']}) is True


def test_is_fun_running_false(salt_return_parser):
    assert salt_return_parser.is_fun_running({'return': ['no match expected']}) is False

