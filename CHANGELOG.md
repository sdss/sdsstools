# Changelog

## Next release

### 🔧 Fixed

* Fix `get_package_version` to get the version from `pyproject.toml` if `poetry` is not used.


## 1.9.6 - 2025-11-14

### 🚀 New

* Added `Retrier` class to implement retry mechanism for functions and coroutines. Copied from [lvmopstools](https://github.com/sdss/lvmopstools).

### 🏷️ Changed

* Change the CHANGELOG header format to be compatible with `kraken`.


## 1.9.5 - 2025-11-06

* Fix changes to `get_event_loop` policy in Python 3.14.


## 1.9.4 - 2025-10-23

* Fix issues casting YAML data to `return_class` in `read_yaml_file`.


## 1.9.3 - 2025-10-10

* Breaking change: `read_yaml_file` now returns a standard `dict` by default.
* Support the use of variables in YAML files.


## 1.9.2 - 2025-08-29

* Fix timezone handling in `get_sjd`.
* Fix calls to `datetime.datetime.utcnow()`.


## 1.9.1 - 2024-12-25

* Update `python-json-logger` to 3.2.1 to silence warnings about module deprecation.


## 1.9.0 - 2024-12-22

* Allow to define a default value for environment variables in the configuration file. If a value is defined as `${ENVAR|default_value}`, the environment variable `ENVAR` will be used if it exists, otherwise `default_value` will be used.
* Updated workflows and moved from Poetry to `uv` for dependency management.


## 1.8.2 - 2024-09-12

* [#52](https://github.com/sdss/sdsstools/pull/52) Add basic support for `GatheringTaskGroup` for Python versions 3.10 and below.


## 1.8.1 - 2024-07-12

* Fixed import of `GatheringTaskGroup` for Python < 3.11.


## 1.8.0 - 2024-07-12

* Added `GatheringTaskGroup` class that extends the functionality of `asyncio.TaskGroup`.


## 1.7.1 - 2024-07-02

* Support Numpy 2 (this only affects the `yanny` module).
* Read yanny text columns as unicode.


## 1.7.0 - 2024-06-26

* Remove `astropy` as a dependency. `yanny` will work without `astropy` except for a couple astropy-specific functions that require it, for which an exception will be raised.


## 1.6.1 - 2023-12-17

* Fix docstring in vendorised `yanny` module that caused warning on import.


## 1.6.0 - 2023-12-13

* [#46](https://github.com/sdss/sdsstools/pull/46) Added several small utilities:
  * `Timer()` (already existed, but mentioning for completeness): a context manager to determine the duration of the task executed between `__enter__` and `__exit__`.
  * `get_temporary_file_path()`: returns a valid temporary named path.
  * `run_in_executor()`: simple wrapper around `asyncio` `run_in_executor` that allows to use `thread` or `process` pool executors and handles arguments and keyword arguments.
  * `cancel_task()`: cancels a task, suppressing the `CancelledError`.


## 1.5.5 - 2023-12-10

* Relax `astropy` and `numpy` requirements.


## 1.5.4 - 2023-12-10

* Fix unpickling of `Configuration` instances. This only seems relevant when trying to pass a `Configuration` object to a `multiprocessing` callback.


## 1.5.3 - 2023-12-08

* Vendorise `pydl`'s `yanny` module which can be accessed as `sdsstools.yanny`.


## 1.5.2 - 2023-11-30

* Allow periods in `RecursiveDict` assignments but treat them as normal dictionary keys.
* Allow retrieving keys with periods in a `RecursiveDict` if they match an existing key.


## 1.5.1 - 2023-11-30

* Fixed an issue assigning dictionaries caused by returning nested dictionaries in a `RecursiveDict` and `RecursiveDict` instances. This has been fixed by doing the conversion at assignment time. A keyword argument, `propagate_type`, allows to disable that behaviour.


## 1.5.011-29 [yanked]

* [#44](https://github.com/sdss/sdsstools/issues/44) If `RecursiveDict` or `Configuration` return a dictionary, the dictionary is itself a `RecursiveDict` or `Configuration` object.
* [#45](https://github.com/sdss/sdsstools/issues/45) Add support for Python 3.12.


## 1.4.0 - 2023-11-16

* Add support for outputting log file in JSON format, via new options in `start_file_logger`.


## 1.3.2 - 2023-11-10

* Better typing for `RecursiveDict`.


## 1.3.1 - 2023-11-10

* Improved typing for `read_yaml_file`.


## 1.3.0 - 2023-11-09

* [#40](https://github.com/sdss/sdsstools/pr/40) Additional options to `start_file_logger` for the `TimedRotatingFileHandler`.
* [#41](https://github.com/sdss/sdsstools/pr/41) `Configuration` now supports a recursive getter (e.g., `config['a.b.c']`).


## 1.2.3 - 2023-08-25

* Store `rich` console instance when passing it to handler.
* Simplify exception handling override code.
* Handle exceptions and log them even within IPython.
* Add option to not capture exceptions in logger.


## 1.2.2 - 2023-08-25

* Ensure that logging to file happens with rich handler.


## 1.2.1 - 2023-08-25

* Improve logging with `rich` and do not use custon exception hook with `RichHandler`.
* Lint using `ruff`.


## 1.2.0 - 2023-08-21

* [#36](https://github.com/sdss/sdsstools/issues/36) Add the option to use a `RichHandler` handler for console logging instead of the default `StreamHandler`. This can be enabled by passing `use_rich_handler` to `get_logger()`. For now this is not the default but it may become so in a future version.
* Update `invoke` to 2.1.3.


## 1.1.0 - 2023-06-18

* [#35](https://github.com/sdss/sdsstools/issues/35) Add support to reload a `Configuration`. If the configuration is based on files on disk and those have changed, the files will be read again.
* Add the option to print the time of a log message in `StreamFormatter` by doing `log.sh.formatter.print_time = True`.


## 1.0.2 - 2022-12-27

* Do not fail CLI if the root of the package cannot be found.


## 1.0.1 - 2022-12-27

* Monkeypatch `invoke` to work with Python 3.10+ (see [this issue](https://github.com/pyinvoke/invoke/issues/833#issuecomment-1293148106)).


## 1.0.0 - 2022-12-27

* **Python 3.6 and 3.7 are not supported anymore.**
* Removed the vendorised copy of `releases`. `releases` is not maintained anymore and should probably not be used. If you want to continue using it, use `0.5.4` or the normal installation of `releases`.
* Full support for Python 3.11.


## 0.5.4 - 2022-12-27

* Add `.pytest_cache` and `.nox` to directories removed by `sdss clean`.
* Add a new task `sdss sjd` that returns the current SJD.


## 0.5.3 - 2022-09-08

* Fix annoying extra printout in `get_sjd()`.


## 0.5.2 - 2022-06-05

* Fix `get_sjd()` which used the current time instead of UTC time, and had an additional `int()` which screwed up the calculation.


## 0.5.1 - 2022-06-04

* Fix the case of YAML files with multiple environment variable substitution or in which the environment variable was not at the beginning of the string.


## 0.5.0 - 2022-04-25

* Added a `time` module with a `get_sjd()` function that returns the SDSS-style Modified Julian Day for an observatory.


## 0.4.15 - 2022-04-21

* Feature [#30](https://github.com/sdss/sdsstools/issues/30): Pass optional `fmt` on to stream formatter.
* Remove use of future typing annotations to continue supporting Python 3.6.
* Add GitHub Actions testing for Python 3.9 and 3.10.


## 0.4.14 - 2022-02-22

* Relaxed `packaging` to prevent issues with other packages.


## 0.4.13 - 2021-08-14

* Make `daemonocle` a required dependency.
* Add `daemonize` CLI script.


## 0.4.12 - 2021-08-13

* Do not redirect output to log in `DaemonGroup` if we are running in debug mode.


## 0.4.11 - 2021-08-12

* Support: allow `pid_file` or `pidfile` in `DeamonGroup` (`pid_file` is recommended since it's the one supported by `daemonocle`).
* Allow to set a global log file in `DaemonGroup` and implement log rotation.


## 0.4.10 - 2021-03-24

* Bug: force use of real path for the logger file handler path.
* Feature [#28](https://github.com/sdss/sdsstools/issues/28): report base config file in `Configuration`. Clear the `Configuration` internal dictionary when `load` is called.


## 0.4.9 - 2021-02-24

* Support: relax dependency on `importlib_metadata`.


## 0.4.8 - 2021-02-13

* Feature [#26](https://github.com/sdss/sdsstools/issues/26): allow rollover of file logger on `start_file_logger`.
* Support: format using `black` and add type hints.


## 0.4.7 - 2021-02-12

* Bug [#24](https://github.com/sdss/sdsstools/issues/24): update dependencies so that `importlib_metadata` is installed for Python<=3.7 (it was Python<3.7).


## 0.4.6 - 2021-01-21

* Do not remove `name` from the parameters in `DaemonGroup` that are passed to `click.Group`. This made `DaemonGroup` fail with `daemonocle>=1.1.0` in which the signature of `Daemon` includes a new parameter `name`.


## 0.4.5 - 2020-11-10

* Bug [#22](https://github.com/sdss/sdsstools/issues/22): fix `read_yaml` for empty YAML files.


## 0.4.4 - 2020-11-05

* Support [#20](https://github.com/sdss/sdsstools/issues/20): discontinue use of `pkg_resources` due to its long import time. Move `sdsstools._vendor.releases` to `sdsstools.releases` to avoid having to load it on import.


## 0.4.3 - 2020-10-31

* Added `Timer` context manager utility.
* Calling `SDSSLogger.set_level` now also sets the level of any warnings handler already present.
* Do not create a logger at the top level of the package.
* New option `--log` when starting a daemon, that will redirect stdout and stderr to a log file.


## 0.4.2 - 2020-08-19

* Better support for asyncio exception handling.


## 0.4.1 - 2020-08-09

* Add signal handler for CLI coroutines.
* Allow to run coroutines in debug mode with the `cli_coro` decorator.


## 0.4.0 - 2020-08-07

* Feature [#15](https://github.com/sdss/sdsstools/issues/15): add a CLI wrapper to create Unix daemons.


## 0.3.1 - 2020-08-01

* Remove a leftover print statement in the logger.


## 0.3.0 - 2020-08-01

* Support [#4](https://github.com/sdss/sdsstools/issues/4): include `dev` extras in default installation.
* Feature [#7](https://github.com/sdss/sdsstools/issues/7): add support for a tag `!extends` in YAML files when read with `read_yaml_file`.
* Bug [#8](https://github.com/sdss/sdsstools/issues/8): log `StreamHandler` to `stderr` when the record level is `ERROR` or greater.
* Support [#11](https://github.com/sdss/sdsstools/issues/11): replaced `colored_formatter` with a propper `Formatter` and added tests for logging.
* Support [#12](https://github.com/sdss/sdsstools/issues/12): move `color_print` to `sdsstools._vendor`.


## 0.2.1 - 2020-07-30

* Store configuration file loaded in `Configuration` as `Configuration.CONFIG_FILE`.
* Improve logging of exceptions to the stream logger.


## 0.2.0 - 2020-07-29

* Feature [#5](https://github.com/sdss/sdsstools/issues/5): `get_config` now returns an instance of `Configuration`, which can also be used at a lower level. `Configuration` stores the base configuration if it was specified, and can be used to load a new configuration file dynamically. Since `Configuration` subclasses from a dictionary and the functionality in `get_config` has not changed, this should be a non-breaking change.
* Support: added initial framework for tests and tests with 98% coverage for `configuration.py`.
* Support: add GitHub workflows for linting and testing.


## 0.1.12 - 2020-07-16

* Prefer `pyproject.toml` or `setup.cfg` over package metadata to retrieve module version.


## 0.1.11 - 2020-07-07

### Fixed

* `TimedRotatingFileHandler` does not accept `mode`.


## 0.1.10 - 2020-06-24

### Added

* Option to normalise the version string to PEP 440 by passing `pep_440=True` to `get_package_version`.


## 0.1.9 - 2020-05-13

### Changed

* Test several user configuration paths: `~/.config/sdss/<NAME>.y(a)ml`, `~/.config/sdss/<NAME>/<NAME>.y(a)ml`, and `~/.<NAME>/<NAME>.y(a)ml`.

### Fixed

* Handle case where log header is None.
* Use `get_config` when there is not a parent package.


## 0.1.8 - 2020-05-01

### Added

* Allow to set a header string in the logger that gets prepended to every message.
* Allow to start the file logger with a `FileHandler`, and pass the file mode.

### Changed

* Configuration default path is now `~/.config/sdss/<NAME>/<NAME>.yaml`.


## 0.1.7 - 2020-04-14

### Changed

* Set minimum Python version to 3.6. Add `six` dependency.


## 0.1.6 - 2020-03-31

### Added

* Missing `docutils` dependency, needed by releases.


## 0.1.5 - 2020-01-23

### Changed

* Better implementation of `SDSSLogger.asyncio_exception_handler`.


## 0.1.4 - 2020-01-23

### Added

* Added `SDSSLogger.asyncio_exception_handler` to report loop exceptions to the logger.


## 0.1.3 - 2020-01-14

### Fixed

* One call to `PyYAML` was still using `load` instead of `safe_load`.
* `read_yaml_file` also accepts a file-like object.


## 0.1.2 - 2019-12-31

### Fixed

* The default target for the docs was pointing to `docs/sphinx/_build` instead of `docs/sphinx`.


## 0.1.1 - 2019-12-31

### Added

* `sdss deploy` now also builds a wheel.
* `twine` and `wheel` dev dependencies for `sdss deploy`.
* Added a version of [releases](https://github.com/bitprophet/releases)

### Changed

* Bundle `toml` in `_vendor` instead of `pytoml`, which is deprecated.


## 0.1.0 - 2019-12-30

### Added

* Logging tools.
* Metadata and version finding tools.
* Command line interface (wrapper around tasks).
* Configuration tools.
