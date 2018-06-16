import abc
import logging
import redis


class SaltNannyClientFactory(object):

    log = logging.getLogger('saltnanny')

    @staticmethod
    def factory(cache_client_type, host, port, db):
        if cache_client_type == 'redis':
            return SaltRedisClient(host, port, db)
        else:
            SaltNannyClientFactory.log.error('Unrecognized Cache Client type: {0}'.format(cache_client_type))


class SaltNannyClient:
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get_latest_jid(self, minion, fun):
        """ expected to return the most current jid for the specified minion, fun combination """

    @abc.abstractmethod
    def get_return_by_jid(self, minion, jid):
        """ expected to return the salt returner results for the specified minion,jid combination"""

    @abc.abstractmethod
    def get_value_by_key(self, base_key):
        """ expected to return the salt returner results associated with the key """

    @abc.abstractmethod
    def exists(self, base_key):
        """ expected to return true if the key exists, false otherwise """


class SaltRedisClient(SaltNannyClient):

    log = logging.getLogger('saltnanny')

    def __init__(self, host='localhost', port=6379, db='0'):
        try:
            self.redis_instance = redis.Redis(host, port, db)
            self.redis_instance.ping()
        except Exception as e:
            self.log.error('Error while trying to connect to redis cache: {0}'.format(e))
            raise e

    def _decode(self, value):
        if value is None:
            return value
        return value.decode('utf-8')

    def get_latest_jid(self, minion, fun):
        cache_key = '{0}:{1}'.format(minion, fun)
        latest_jid = '0'
        try:
            key_type = self._decode(self.redis_instance.type(cache_key))
            if key_type == 'list':
                latest_jid = self._decode(self.redis_instance.lindex(cache_key, 0))
            elif key_type == 'string':
                latest_jid = self._decode(self.redis_instance.get(cache_key))
        except KeyError:
            self.log.info('Latest jid not found. Defaulting to 0')
            pass
        self.log.info('Latest jid for Minion:{0} JID:{1}'.format(minion, latest_jid))
        return latest_jid

    def get_return_by_jid(self, minion, jid):
        cache_key = '{0}:{1}'.format(minion, jid)
        cache_key_salt_2016 = 'ret:{0}'.format(jid)
        if self.redis_instance.exists(cache_key):
            return self._decode(self.redis_instance.get(cache_key))
        elif self.redis_instance.exists(cache_key_salt_2016):
            return self._decode(self.redis_instance.hget(cache_key_salt_2016, minion))
        else:
            msg = 'Return info for JID:{0} does not exist'.format(jid)
            self.log.error(msg)
            raise ValueError(msg)

    def get_value_by_key(self, base_key):
        return self._decode(self.redis_instance.get(base_key))

    def exists(self, base_key):
        return self.redis_instance.exists(base_key)
