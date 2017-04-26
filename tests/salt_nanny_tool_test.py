import unittest
from argparse import ArgumentParser
from saltnanny import salt_nanny_tool, SaltNanny
from mock import patch, call


class ScriptsTest(unittest.TestCase):

    class MockArguments(object):
        pass

    mock_args = MockArguments()
    mock_args.host = 'localhost'
    mock_args.port = 6379
    mock_args.type = 'redis'
    mock_args.intervals = [1, 30, 2]
    mock_args.log_file = None
    mock_args.custom_event = 'state.highstate'
    mock_args.minions = ['minion1']
    mock_args.max_attempts = 15

    @patch.object(ArgumentParser, 'add_argument')
    @patch.object(ArgumentParser, 'parse_args', return_value=mock_args)
    @patch.object(SaltNanny, '__init__', return_value=None)
    @patch.object(SaltNanny, 'initialize')
    @patch.object(SaltNanny, 'track_returns')
    def test_tool_main(self, mock_init, mock_initialize, mock_track_returns, mock_parse_args, mock_add_argument):
        salt_nanny_tool.tool_main()
        assert(mock_add_argument.call_count == 9)
        assert(mock_parse_args.call_count == 1)
