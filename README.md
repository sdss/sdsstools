# sdsstools

[![Versions](https://img.shields.io/badge/python->3.7-blue)](https://docs.python.org/3/)
[![PyPI version](https://badge.fury.io/py/sdsstools.svg)](https://badge.fury.io/py/sdsstools)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Tests Status](https://github.com/sdss/sdsstools/workflows/Test/badge.svg)](https://github.com/sdss/sdsstools/actions)
[![codecov](https://codecov.io/gh/sdss/sdsstools/branch/main/graph/badge.svg)](https://codecov.io/gh/sdss/sdsstools)

`sdsstools` provides several common tools for logging, configuration handling, version parsing, packaging, etc. Its main purpose is to consolidate some of the utilities originally found in the [python_template](https://github.com/sdss/python_template), allowing them to become dependencies that can be updated.

**This is not intended to be a catch-all repository for astronomical tools.** `sdsstools` itself aims to have minimal dependencies (i.e., mainly the Python standard library and setuptools).

## Using sdsstools

To use sdsstools simply install it with

```console
pip install sdsstools
```

Most likely, you'll want to include sdsstools as a dependency for your library. To do so, either add to your `setup.cfg`

```ini
[options]
install_requires =
    sdsstools>=0.1.0
```

(this is equivalent of passing `install_requires=['sdsstools>=0.1.0']` to `setuptools.setup`), or if you are using [poetry](https://poetry.eustace.io/) run `poetry add sdsstools`, which should add this line to your `pyproject.toml`

```toml
[tool.poetry.dependencies]
sdsstools = { version="^0.1.0" }
```

## Logging

sdsstools includes the [sdsstools.logger.SDSSLogger](https://github.com/sdss/sdsstools/blob/f30e00f527660fe8627e33a7f931b44410b0ff06/src/sdsstools/logger.py#L107) class, which provides a wrapper around the standard Python [logging](https://docs.python.org/3/library/logging.html) module. `SDSSLoger` provides the following features:

- A console handler (accessible via the `.sh` attribute) with nice colouring.
- Automatic capture of warnings and exceptions, which are formatted and redirected to the logger. For the console handler, this means that once the logger has been created, all warnings and exceptions are output normally but are clearer and more aesthetic.
- A [TimedRotatingFileHandler](https://docs.python.org/3.8/library/logging.handlers.html#logging.handlers.TimedRotatingFileHandler) (accessible via the `.fh` attribute) that rotates at midnight UT, with good formatting.
- A version of the logger that uses `rich` [log handling](https://rich.readthedocs.io/en/stable/logging.html).

To get a new logger for your application, simply do

```python
from sdsstools.logger import get_logger

NAME = 'myrepo'
log = get_logger(NAME)
```

You can get a logger using the `rich` `RichHandler` by passing `use_rich_handler=True`.

The file logger is disabled by default and can be started by calling `log.start_file_logger(path)`. By default a `TimedRotatingFileHandler` is created. If you want a normal `FileHandler` use `rotating=False`. The file mode defaults to `mode='a'` (append).  The `TimedRotatingFileHandler` options `when`, `utc`, and `at_time` are available to
`log.start_file_logger` for controlling aspects of the rollover time.

By default, the file logger is formatted to output a human-readble `log` file.  To output a JSON log instead, set `as_json=True`, when calling `log.start_file_logger`.  This will create a `.json` log file which can machine-read and more easily parsed for content.  To output both a human-readable (`.log`) and JSON log (`.json`), set `with_json=True`.

The `SDSSLogger` instance also include an `asyncio_exception_handler` method that can be added to the asyncio event loop to handle exceptions; for example `loop.set_exception_handler(log.asyncio_exception_handler)`.

Console logging uses the standard `StreamHandler`. It's possible to use the `rich` library [RichHandler](https://rich.readthedocs.io/en/stable/logging.html) instead by
passing `use_rich_handler=True` to `get_logger()`. Additional keyword arguments to `RichHandler` can be passed as a `rich_handler_kwargs` dictionary. In the future the `rich` handler may become the default console logger.

## Configuration

The `sdsstools.configuration` module contains several utilities to deal with configuration files. The most useful one is [get_config](https://github.com/sdss/sdsstools/blob/d3d337953a37aaff9c38fead76b08b414164775a/src/sdsstools/configuration.py#L40), which allows to read a YAML configuration file. For example

```python
from sdsstools.configuration import get_config

NAME = 'myrepo'
config = get_config(NAME, allow_user=True)
```

`get_config` assumes that the file is located in `etc/<NAME>.yml` relative from the file that calls `get_config`, but that can be changed by passing `config_file=<config-file-path>`. Additionally, if `allow_user=True` and a file exists in `~/.config/sdss/<NAME>.yaml`, this file is read and merged with the default configuration, overriding any parameter that is present in the user file. This allows to create a default configuration that lives with the library but that can be overridden by a user.

In addition to the (recommended) location `~/.config/sdss/<NAME>.yaml`, `get_config` also looks for user configuration files in `~/.config/sdss/<NAME>.yml`, `~/.config/sdss/<NAME>/<NAME>.y(a)ml`, and `~/.<NAME>/<NAME>.y(a)ml`.

`get_config` returns an instance of [Configuration](https://github.com/sdss/sdsstools/blob/5af8339d2696d92e122b4195272130101b54daa7/src/sdsstools/configuration.py#L162), which behaves as a dictionary but allows to dynamically reload the configuration from a new user file by calling `load()`.

`sdsstools.configuration` includes two other tools, `merge_config`, that allows to merge dictionaries recursively, and `read_yaml_file` to read a YAML file.

### Extending a YAML file

`read_yaml_file` provides a non-standard feature that allows you to extend one YAML file with another. To achieve this you need to add the tag `!extends <base-file>` at the top of the file that you want to extend. For example, if you have a file `base.yaml`

```yaml
cat1:
  key1: value2

cat2:
  key2: 1
```

that you want to use as a template for `extendable.yaml`

```yaml
#!extends base.yaml

cat1:
  key1: value1
```

you can use `read_yaml_file` to parse the result

```python
>>> read_yaml_file('extendable.yaml')
{'cat1': {'key1': 'value2'}, 'cat2': {'key2': 1}}
```

The path to the base file must be absolute or relative to the location of the file to be extended.

### Using variables in YAML files

`read_yaml_file` and `get_config` support the use of variables in YAML files. A special section `variables` can be defined at the top level of the YAML file, and any `$(VAR)` string in the file will be replaced by the value of the variable. For example

```yaml
variables:
  greeting: hello

cat1:
  key1: $(greeting) world
```

```python
>>> read_yaml_file('file.yaml', use_variables=True)
{'cat1': {'key1': 'hello world'}, 'variables': {'greeting': 'hello'}}
```

Environment variables can also be used by including a `${ENV_VAR}` string in the YAML file, which will be replaced with the content of the `$ENV_VAR` environment variable.

### The `Configuration` class

By default `get_config()` and `read_yaml_file()` return a `Configuration` instance. For the most part a `Configuration` object is the same as a dictionary, and it can be used as such. It has two main differences:

- When a `Configuration` object is initialised from a file (or a base and custom configuration files) as with `get_config()`, the object keeps the information about the file paths. It's then possible to call `Configuration.reload()` to hot-reload the contents of the file after it has changed.
- It is possible to recursively get a nested configuration value, for example `config['a.b']`, which is equivalent to `dd['a']['b']` but will return `None` if a key does not exist anywhere in the chain. This behaviour can be disabled by setting `config.strict_mode=True`. Note that this syntax is not valid for assignement and attempting to do `d['a.b'] = 1` will raise an error.

## Metadata

sdsscore provides tools to locate and parse metadata files (`pyproject.toml`, `setup.cfg`, `setup.py`). `get_metadata_files` locates the path of the metadata file relative to a given `path`. `get_package_version` tries to find the version of the package by looking for a version string in the metadata file or in the egg/wheel metadata file, if the package has been installed. To use it

```python
from sdsstools.metadata import get_package_version

__version__ = get_package_version(path=__file__, package_name='sdss-camera') or 'dev'
```

This will try to find and parse the version from the metadata file (we pass `__file__` to indicate where to start looking); if that fails, it will try to get the version from the installed package `sdss-camera`. If all fails, it will set the fallback version `'dev'`.

## Command Line Interface

`sdsstools` provides the command line tool `sdss`, which is just a thin wrapper around some commonly used [Invoke](https://www.pyinvoke.org/) tasks. `sdsstools` does not automatically install all the dependencies for the tasks, which need to be added manually.

`sdss` provides the following tasks

| Task         | Options  | Description                                                                    |
| ------------ | -------- | ------------------------------------------------------------------------------ |
| clean        |          | Removes files produces during build and packaging.                             |
| deploy       | --test   | Builds and deploys to PyPI (or the test server). Requires `twine` and `wheel`. |
| install-deps | --extras | Installs dependencies from a `setup.cfg` file                                  |
| docs.build   | --target | Builds the Sphinx documentation. Requires `Sphinx`.                            |
| docs.show    | --target | Shows the documentation in the browser. Requires `Sphinx`.                     |
| docs.clean   | --target | Cleans the documentation build. Requires `Sphinx`.                             |

`sdss` assumes that the documentation lives in `docs/sphinx` relative to the root of the repository. This can be changed by setting the `sphinx.target` configuration in an `invoke.yaml` file, for example

```yaml
sphinx:
  target: docs
```

## Click daemon command

The [daemonizer](src/sdsstools/daemonizer.py) module implements a [Click](https://palletsprojects.com/p/click/) command group that allows to spawn a daemon, and to stop and restart it. Internally the module uses [daemonocle](https://github.com/jnrbsn/daemonocle) (the package is not installed with `sdsstools` and needs to be pip-installed manually).

A simple example of how to use `daemonizer` is

```python
import time
import click
from sdsstools.daemonizer import DaemonGroup

@click.group(cls=DaemonGroup, prog='hello', pidfile='/var/tmp/hello.pid')
@click.argument('NAME', type=str)
@click.option('--file', type=str, default='hello.dat')
def daemon(name):

    with open(file, 'w') as unit:
        while True:
            unit.write(f'Hi {name}!\n')
            unit.flush()
            time.sleep(1)

if __name__ == '__main__':
    daemon()
```

This will create a new group `hello` with four subcommands

```console
Usage: daemon [OPTIONS] NAME COMMAND [ARGS]...

Options:
  --file
  --help  Show this message and exit.

Commands:
  restart  Restart the daemon.
  start    Start the daemon.
  status   Report if the daemon is running.
  stop     Stop the daemon.
```

Now we can run `daemon --file ~/hello.dat John start` and a new background process will start, writing to the file every second. We can stop it with `daemon stop`. In general the behaviour is identical to the [daemonocle Click implementation](https://github.com/jnrbsn/daemonocle#integration-with-mitsuhiko-s-click) but the internal are slightly different to allow the group callback to accept arguments. If the callback is a coroutine, it can be wrapped with the `cli_coro` decorator

```python
import asyncio
import signal
import click
from sdsstools.daemonizer import DaemonGroup, cli_coro

def shutdown(signal):
    if signal == signal.SIGTERM:
        cancel_something()

@click.group(cls=DaemonGroup, prog='hello', pidfile='/var/tmp/hello.pid')
@click.argument('NAME', type=str)
@click.option('--file', type=str, default='hello.dat')
@cli_coro(shutdown_func=shutdown, signals=(signal.SIGTERM, signal.SIGINT))
async def daemon(name):

    with open(file, 'w') as unit:
        while True:
            unit.write(f'Hi {name}!\n')
            unit.flush()
            await asyncio.sleep(1)
```

`cli_coro` can accept a `shutdown_func` function that is called when the coroutine receives a signal. The default signals handled are `(SIGHUP, SIGTERM, SIGINT)`.

### Daemonizing a command

To execute any command as a daemon you can use the `daemonize` script that is installed with `sdsstools`. To start the process as a daemon do `daemonize start NAME COMMAND` when `NAME` is the name associated to the daemon (so that it can be stopped later) and `COMMAND` is the command to run, for example:

```console
daemonize start apoActor python ./apoActor_main.py
```

To stop the daemon do `daemonize stop NAME`. See `daemonize --help` for more options.

## Date functions

The function `sdsstools.time.get_sjd()` returns the integer with the SDSS-style Modified Julian Day. The function accepts an observatory (`'APO'` or `'LCO'`) but otherwise will try to determine the current location from environment variables or the fully qualified domain name.

## Retrier

The `Retrier` class provides a simple way to add retry logic to functions that may fail intermittently. It can be used to wrap both synchronous and asynchronous functions. `Retrier` produces a callable that can be used as a decorator or called directly. For example:

```python
from sdsstools.retrier import Retrier

@Retrier(max_attempts=5, delay=2.0)
async def my_function(param1, param2):
    ...

await my_function(1, 2)
```

or

```python
def my_function(param1, param2):
    ...

retrier = Retrier(max_attempts=5, delay=2.0)
retrier(my_function)(1, 2)
```

By default `Retrier` will try three times with a one second delay between attempts. An exponential backoff is used by default. If the function keeps failing after the maximum number of attempts, the last exception is raised. It is possible to stop the retry process early if a certain type of exception is raised by passing a list of such exception classes to `raise_on_exception_class`.

## Bundled packages

For convenience, `sdsstools` bundles the following products:

- **(Up to version 1.0.0)** A copy of [releases](https://github.com/bitprophet/releases) that fixes some issues with recent versions of `semantic-version`. This copy is not available in `sdsstools>=1.0.0`. `releases` is not maintained anymore, so use at your own risk.
- A copy of [toml](https://github.com/uiri/toml) to read TOML files (used by the metadata submodule).
- An adapted version of Astropy's [color_print](https://docs.astropy.org/en/stable/api/astropy.utils.console.color_print.html).
- A copy of the pydl's [yanny module](https://github.com/weaverba137/pydl).

You can access them directly from the top-level namespace, `sdsstools.toml`, `sdsstools.releases`. To use `releases` with sphinx, simply add the following to your `config.py`

```python
extensions += ['sdsstools.releases']
```
