# salt-nanny [![Build Status](https://travis-ci.org/dandb/salt-nanny.svg?branch=master)](https://travis-ci.org/dandb/salt-nanny) [![Coverage Status](https://coveralls.io/repos/github/dandb/salt-nanny/badge.svg?branch=master)](https://coveralls.io/github/dandb/salt-nanny?branch=master)
Python Module that parses salt returns stored in redis and logs output 

# Example Usage:
*Command Line Usage:*
```
salt-nanny localhost minion1 minion2
```
Look for salt returns in localhost for minions - minion1 & minion2

```
salt-nanny localhost minion1 minion2 -p 6380 -x 20 -I 5 60 2
```
This command tells salt-nanny to wait 5, 10, 20, 40 and 60 seconds between each retry initially and then 60s for
subsequent retries. Attempt 20 times and then give up. Use port 6380 for redis.

```
salt-nanny localhost minion1 -r -j 20170905144844350779
```
This command tells salt-nanny to return results from minion minion1 that have higher JID than 20170905144844350779

*Example Python code:*
```
#!/usr/bin/env python
import salt.client
from saltnanny import SaltNanny

# Initialize SaltNanny with the cache & salt function
config = {'type': 'redis', 'host':'localhost', 'port':6379, 'db':'0'}
nanny = SaltNanny(config, 'test', 'state.highstate')

# Use SaltNanny to track returns to the external job cache
salt_nanny.initialize(['minion1', 'minion2'])
salt_nanny.track_returns()
return_code = salt_nanny.process_returns()
```

* For the example above, the log file in logs/test-state.highstate.log will contain results of the salt highstate
* The return code is 0 if all the salt functions for all minions succeded with a return dict containing retcode:0.
* SaltNanny also checks state results in case of a highstate. If any one state fails, the retcode is non zero.
