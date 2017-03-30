
### coloredorjsonlogs.py

A colored or json output logging module.  
Example:
```python
logger = coloredorjsonlogs.get_logger('Worker')
logger.warning("Ted is dead.")
logger.info("balanace: %d", 123, name="Mr. White", card_number=12345678)
```

Output:

```shell
[WARNING] [2017-03-30 16:01:55] log.py:315 Worker Ted is dead.
[INFO] [2017-03-30 16:01:55] log.py:316 Worker balanace: 123	name=Mr. White card_number=12345678
```

Sometimes log files will be inputed into log analysis system, maybe a more formattable output likes JSON is friendly to that, if you wanna a jsonized log output, replace `no_color=0` to `no_color=1` at the bottom of `coloredorjsonlogs.py`, or control this with `argparser` or others, anyway you have the codes, do every you want.

Output:
```shell
{"message": "Ted is dead.", "level": "WARNING", "timestamp": "2017-03-30T16:03:43.808628", "fields": {}}
{"message": "balanace: 123", "level": "INFO", "timestamp": "2017-03-30T16:03:43.811050", "fields": {"name": "Mr. White", "card_number": 12345678}}
```

