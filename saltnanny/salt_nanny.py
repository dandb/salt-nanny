import logging
import math
import os
from time import sleep


from .salt_return_parser import SaltReturnParser
from .salt_nanny_client import SaltNannyClientFactory


class SaltNanny:

    log = logging.getLogger('saltnanny')
    log_fmt = '%(asctime)s %(levelname)s %(message)s'

    def __init__(self, cache_config, target_log_file=None, fun='state.highstate',
                 min_interval=15, max_interval=60, multiplier=2):
        self.fun = fun
        self.initial_jids = {}
        self.completed_minions = {}
        self.min_interval = min_interval
        self.max_interval = max_interval
        self.multiplier = multiplier
        self.setup_logging(target_log_file)
        self.cache_client = SaltNannyClientFactory.factory(
            cache_config['type'], cache_config['host'], cache_config['port'], cache_config['db'])
        self.parser = SaltReturnParser(self.cache_client)

    def initialize(self, minion_list):
        if minion_list:
            self.minion_list = minion_list
            for minion in minion_list:
                self.initial_jids[minion] = self.cache_client.get_latest_jid(minion, self.fun)
        else:
            raise ValueError("No Minions provided. SaltNanny has no minions to babysit.")

    def track_returns(self, max_attempts=17):
        pending_minion_list = list(self.minion_list)

        for i in range(0, max_attempts):
            pending_minion_list = [minion for minion in pending_minion_list if minion not in list(self.completed_minions.keys())]

            if pending_minion_list:
                wait_time = self.get_wait_time(i)
                self.log.info('Sleeping for {0} seconds...'.format(wait_time))
                sleep(wait_time)
                self.log.info('SaltNanny is checking for minion returns in External Job Cache - Attempt: {0}'.format(i))
                for minion in pending_minion_list:
                    latest_jid = self.cache_client.get_latest_jid(minion, self.fun)
                    if latest_jid == self.initial_jids[minion]:
                        self.log.info('SaltNanny did not find a new JID for minion: {0}'.format(minion))
                        break
                    else:
                        self.log.info('SaltNanny found a New JID for minion: {0} JID: {1}'.format(minion, latest_jid))
                        self.completed_minions[minion] = latest_jid
            else:
                self.log.info('Results available in External Job Cache for all minions: {0}'
                              .format(list(self.completed_minions.keys())))
                break
        self.log.info(self.completed_minions)
        return self.parser.process_jids(self.completed_minions, len(self.minion_list))

    def parse_last_return(self, earliest_jid=0):
        for minion in self.minion_list:
            latest_jid = self.cache_client.get_latest_jid(minion, self.fun)
            if int(latest_jid) < earliest_jid:
                self.log.info("No highstates found in job cache for minion: {0} after: {1}".format(minion, earliest_jid))
                return 1
            else:
                self.completed_minions[minion] = latest_jid
        self.log.info(self.completed_minions)
        return self.parser.process_jids(self.completed_minions, len(self.minion_list))

    def get_wait_time(self, index):
        wait_interval = self.min_interval * math.pow(self.multiplier, index)
        if wait_interval > self.max_interval:
            return self.max_interval
        return wait_interval

    def track_custom_event_failures(self, event_key, failures, max_attempts=17, successes=None):
        if successes is None:
            successes = []
        for i in range(0, max_attempts):
            wait_time = self.get_wait_time(i)
            self.log.info('Sleeping for {0} seconds...'.format(wait_time))
            sleep(wait_time)
            self.log.info('SaltNanny is checking for Custom Event: {0} in External Job Cache - Attempt: {1}'
                          .format(event_key, i))
            if self.cache_client.exists(event_key):
                self.log.info('SaltNanny found the Custom Event: {0} in External Job Cache. Checking for failures...'
                              .format(event_key))
                return self.parser.check_custom_event_failure(event_key, failures, successes)
        self.log.info('SaltNanny has timed out waiting for Custom Event: {0}'.format(event_key))
        return 1

    def setup_logging(self, target_log_file):
        formatter = logging.Formatter(self.log_fmt)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.log.addHandler(console_handler)
        self.log.setLevel(logging.INFO)
        if target_log_file:
            target = os.path.join(os.getcwd(), 'logs/{0}-{1}.log'.format(target_log_file, self.fun))
            if not os.path.exists(os.path.dirname(target)):
                os.makedirs(os.path.dirname(target))
            ch = logging.FileHandler(target)
            ch.setFormatter(formatter)
            self.log.addHandler(ch)
