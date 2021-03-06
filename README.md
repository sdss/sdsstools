# sdsstools

[![Versions](https://img.shields.io/badge/python->3.7-blue)](https://docs.python.org/3/)
[![PyPI version](https://badge.fury.io/py/sdsstools.svg)](https://badge.fury.io/py/sdsstools)
[![Build](https://img.shields.io/github/workflow/status/sdss/sdsstools/Test)](https://github.com/sdss/sdsstools/actions)
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

To get a new logger for your application, simply do

```python
from sdsstools.logger import get_logger

NAME = 'myrepo'
log = get_logger(NAME)
```

The file logger is disabled by default and can be started by calling `log.start_file_logger(path)`. By default a `TimedRotatingFileHandler` is created. If you want a normal `FileHandler` use `rotate=False`. The file mode defaults to `mode='a'` (append).

The `SDSSLoger` instance also include an `asyncio_exception_handler` method that can be added to the asyncio event loop to handle exceptions; for example `loop.set_exception_handler(log.asyncio_exception_handler)`.

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

| Task | Options | Description |
| --- | --- | --- |
| clean | | Removes files produces during build and packaging. |
| deploy | --test | Builds and deploys to PyPI (or the test server). Requires `twine` and `wheel`. |
| install-deps | --extras | Installs dependencies from a `setup.cfg` file |
| docs.build | --target | Builds the Sphinx documentation. Requires `Sphinx`. |
| docs.show | --target | Shows the documentation in the browser. Requires `Sphinx`. |
| docs.clean | --target | Cleans the documentation build. Requires `Sphinx`. |

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


## Bundled packages

For convenience, `sdsstools` bundles the following products:

- A copy of [releases](https://github.com/bitprophet/releases) that fixes some issues with recent versions of `semantic-version`.
- A copy of [toml](https://github.com/uiri/toml) to read TOML files (used by the metadata submodule).

You can access them directly from the top-level namespace, `sdsstools.toml`, `sdsstools.releases`. To use `releases` with sphinx, simply add the following to your `config.py`

```python
extensions += ['sdsstools.releases']
```
