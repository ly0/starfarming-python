
### coloredorjsonlogs.py

A colored or json output logging module.  
Example:
```python
logger = coloredorjsonlogs.get_logger('Worker')
logger.warning("Ted is dead.")
logger.info("balanace: %d", 123, name="Mr. White", card_number=12345678)
```
If you wanna a jsonized log output, replace `no_color=0` to `no_color=1` at the bottom of `coloredorjsonlogs.py`
