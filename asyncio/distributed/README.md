#### worker_redis.py
(Waiting instructions done.)
Usage:
```python
asyncio def sync_wallet():
  blablabla

asyncio def send_mail():
  blablabal
  
worker = Worker(handlers={
  'sync_wallet': sync_wallet,
  'send_mail': send_mail
})
```

This file can be a part of a RPC framework easily, so I didn't specify any protocols except using redis as a MQ.
