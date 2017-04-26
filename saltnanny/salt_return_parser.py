#!/usr/bin/env python

import re
import logging
import json
from time import sleep
from ast import literal_eval


class SaltReturnParser:

    log = logging.getLogger('saltnanny')
    fun_running_pattern = 'is running as PID'

    def __init__(self, cache_client, min_interval=15, max_attempts=15):
        self.cache_client = cache_client
        self.min_interval = min_interval
        self.max_attempts = max_attempts

    def process_jids(self, completed_minions, all_minions_count):
        return_code_sum = 0
        for minion, jid in completed_minions.iteritems():
            try:
                return_info, return_code = self.get_return_info(minion, jid)
                return_code_sum += return_code
                self.log.info(json.dumps(return_info, indent=1))
            except ValueError as ve:
                self.log.error('Error retrieving results for Minion:{0}: Exception:{1}'.format(minion, ve))

        if not completed_minions:
            self.log.info('No highstates found in Job Cache, setting return_code_sum = 2')
            return_code_sum = 2

        if len(completed_minions) != all_minions_count and return_code_sum == 0:
            self.log.info('Highstates available in Job Cache were successful, timed out waiting for others.')
            return_code_sum = 1
        elif return_code_sum != 0:
            self.log.info('One or more highstates were not entirely successful. Please investigate.')
        else:
            self.log.info('All Highstates completed successfully!')

        return return_code_sum

    def check_custom_event_failure(self, cache_key, failures, successes):
        custom_results = literal_eval(self.cache_client.get_value_by_key(cache_key))
        self.log.info('Custom Event Return in Job Cache. Key: {0} Value:'.format(cache_key))
        if isinstance(custom_results, list):
            # Print results on each line if its a list (for example a list of log statements)
            for result in custom_results:
                self.log.info(result)

            for result in custom_results:
                if self.check_successes(result, successes):
                    return 0
                if self.check_failures(result, failures):
                    return 1
        else:
            self.log.info(custom_results)
            if self.check_successes(custom_results, successes):
                return 0
            if self.check_failures(custom_results, failures):
                return 1
        return 0

    @staticmethod
    def check_failures(result, failures):
        failures_exist = [True for failure in failures if failure in result]
        return True in failures_exist

    @staticmethod
    def check_successes(result, successes):
        successes_exist = [True for success in successes if success in result]
        return True in successes_exist

    def get_return_info(self, minion, jid, attempt=1):
        self.log.info('Getting return info for Minion:{0} JID:{1}'.format(minion, jid))

        return_info = self.cache_client.get_return_by_jid(minion, jid)
        return_dict = json.loads(return_info)
        return_code = return_dict.get('retcode')

        if self.is_fun_running(return_dict) and attempt < self.max_attempts:
            self.log.info('Return Info for JID:{0} indicates that the function is still running.'.format(jid))
            self.log.info('Sleeping for {0} seconds...'
                          .format(self.min_interval, jid))
            sleep(self.min_interval)
            attempt += 1
            return self.get_return_info(minion, jid, attempt)

        if self.highstate_failed(return_info) or not isinstance(return_code, int):
            return_code = 1

        return return_dict, return_code

    def highstate_failed(self, result):
        try:
            possible_failures = ['"result": false', 'Data failed to compile:', 'Pillar failed to render with the following messages:']
            failures = [failure in result for failure in possible_failures]
            self.log.info(failures)
            if True not in failures:
                failures = self.check_regex_failure(failures, result)
            return True in failures
        except:
            self.log.error('Error finding if there was a failure in the result:\n {0}'.format(result))
            return True

    def check_regex_failure(self, failures, result):
        regex_failure = r"Rendering SLS '.*' failed:"
        failures.append(bool(re.search(regex_failure, result)))
        return failures

    def is_fun_running(self, return_dict):
        if 'return' in return_dict and isinstance(return_dict['return'], list):
            for return_item in return_dict['return']:
                if self.fun_running_pattern in return_item:
                    return True
        return False
