# Note
If you are installed the `aioredis` package on Python 3.11 or latter, and you are getting the following error:
```
TypeError: duplicate base class TimeoutError
```
You can fix it temporarily by adding the following code to the package's path `your-venv-path\aioredis\exceptions.py`, line 14:
```
...

class TimeoutError(builtins.TimeoutError, RedisError):
    pass
```
This is a temporary fix until the package is updated.
