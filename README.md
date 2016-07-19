# salt-nanny [![Build Status](https://travis-ci.org/vmadura/salt-nanny.svg?branch=master)](https://travis-ci.org/vmadura/salt-nanny) [![Coverage Status](https://coveralls.io/repos/github/dandb/salt-nanny/badge.svg?branch=master)](https://coveralls.io/github/dandb/salt-nanny?branch=master)
Python Module that parses salt returns stored in redis and logs output 

# Example Usage:

example.py
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
* SaltNanny also checks state results in case of a highstate. If any one state fails, the retcode is 0.
