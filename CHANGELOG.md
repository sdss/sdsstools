# Changelog

## [0.4.7](https://github.com/sdss/sdsstools/compare/0.4.6...HEAD)


## [0.4.6](https://github.com/sdss/sdsstools/compare/0.4.5...0.4.6) - 2021-01-21

- Do not remove `name` from the parameters in `DaemonGroup` that are passed to `click.Group`. This made `DaemonGroup` fail with `daemonocle>=1.1.0` in which the signature of `Daemon` includes a new parameter `name`.


## [0.4.5](https://github.com/sdss/sdsstools/compare/0.4.4...0.4.5) - 2020-11-10

- Bug [#22]: fix `read_yaml` for empty YAML files.


## [0.4.4](https://github.com/sdss/sdsstools/compare/0.4.3...0.4.4) - 2020-11-05

- Support [#20]: discontinue use of `pkg_resources` due to its long import time. Move `sdsstools._vendor.releases` to `sdsstools.releases` to avoid having to load it on import.


## [0.4.3](https://github.com/sdss/sdsstools/compare/0.4.2...0.4.3) - 2020-10-31

- Added `Timer` context manager utility.
- Calling `SDSSLogger.set_level` now also sets the level of any warnings handler already present.
- Do not create a logger at the top level of the package.
- New option `--log` when starting a daemon, that will redirect stdout and stderr to a log file.


## [0.4.2](https://github.com/sdss/sdsstools/compare/0.4.1...0.4.2) - 2020-08-19

- Better support for asyncio exception handling.


## [0.4.1](https://github.com/sdss/sdsstools/compare/0.4.0...0.4.1) - 2020-08-09

- Add signal handler for CLI coroutines.
- Allow to run coroutines in debug mode with the ``cli_coro`` decorator.


## [0.4.0](https://github.com/sdss/sdsstools/compare/0.3.1...0.4.0) - 2020-08-07

- Feature [#15](https://github.com/sdss/sdsstools/issues/15): add a CLI wrapper to create Unix daemons.


## [0.3.1](https://github.com/sdss/sdsstools/compare/0.3.0...0.3.1) - 2020-08-01

- Remove a leftover print statement in the logger.


## [0.3.0](https://github.com/sdss/sdsstools/compare/0.2.1...0.3.0) - 2020-08-01

- Support [#4](https://github.com/sdss/sdsstools/issues/4): include `dev` extras in default installation.
- Feature [#7](https://github.com/sdss/sdsstools/issues/7): add support for a tag `!extends` in YAML files when read with `read_yaml_file`.
- Bug [#8](https://github.com/sdss/sdsstools/issues/8): log `StreamHandler` to `stderr` when the record level is `ERROR` or greater.
- Support [#11](https://github.com/sdss/sdsstools/issues/11): replaced `colored_formatter` with a propper `Formatter` and added tests for logging.
- Support [#12](https://github.com/sdss/sdsstools/issues/12): move `color_print` to `sdsstools._vendor`.


## [0.2.1](https://github.com/sdss/sdsstools/compare/0.2.0...0.2.1) - 2020-07-30

- Store configuration file loaded in `Configuration` as `Configuration.CONFIG_FILE`.
- Improve logging of exceptions to the stream logger.

## [0.2.0](https://github.com/sdss/sdsstools/compare/0.1.12...0.2.0) - 2020-07-29

- Feature [#5](https://github.com/sdss/sdsstools/issues/5): `get_config` now returns an instance of `Configuration`, which can also be used at a lower level. `Configuration` stores the base configuration if it was specified, and can be used to load a new configuration file dynamically. Since `Configuration` subclasses from a dictionary and the functionality in `get_config` has not changed, this should be a non-breaking change.
- Support: added initial framework for tests and tests with 98% coverage for `configuration.py`.
- Support: add GitHub workflows for linting and testing.


## [0.1.12](https://github.com/sdss/sdsstools/compare/0.1.11...0.1.12) - 2020-07-16

- Prefer `pyproject.toml` or `setup.cfg` over package metadata to retrieve module version.


## [0.1.11](https://github.com/sdss/sdsstools/compare/0.1.10...0.1.11) - 2020-07-07

### Fixed

- `TimedRotatingFileHandler` does not accept `mode`.


## [0.1.10](https://github.com/sdss/sdsstools/compare/0.1.9...0.1.10) - 2020-06-24

### Added

- Option to normalise the version string to PEP 440 by passing `pep_440=True` to `get_package_version`.


## [0.1.9](https://github.com/sdss/sdsstools/compare/0.1.8...0.1.9) - 2020-05-13

### Changed

- Test several user configuration paths: `~/.config/sdss/<NAME>.y(a)ml`, `~/.config/sdss/<NAME>/<NAME>.y(a)ml`, and `~/.<NAME>/<NAME>.y(a)ml`.

### Fixed

- Handle case where log header is None.
- Use `get_config` when there is not a parent package.


## [0.1.8](https://github.com/sdss/sdsstools/compare/0.1.7...0.1.8) - 2020-05-01

### Added

- Allow to set a header string in the logger that gets prepended to every message.
- Allow to start the file logger with a `FileHandler`, and pass the file mode.

### Changed

- Configuration default path is now `~/.config/sdss/<NAME>/<NAME>.yaml`.


## [0.1.7](https://github.com/sdss/sdsstools/compare/0.1.6...0.1.7) - 2020-04-14

### Changed

- Set minimum Python version to 3.6. Add `six` dependency.


## [0.1.6](https://github.com/sdss/sdsstools/compare/0.1.5...0.1.6) - 2020-03-31

### Added

- Missing `docutils` dependency, needed by releases.


## [0.1.5](https://github.com/sdss/sdsstools/compare/0.1.4...0.1.5) - 2020-01-23

### Changed

- Better implementation of ``SDSSLogger.asyncio_exception_handler``.


## [0.1.4](https://github.com/sdss/sdsstools/compare/0.1.3...0.1.4) - 2020-01-23

### Added

- Added ``SDSSLogger.asyncio_exception_handler`` to report loop exceptions to the logger.


## [0.1.3](https://github.com/sdss/sdsstools/compare/0.1.2...0.1.3) - 2020-01-14

### Fixed

- One call to `PyYAML` was still using `load` instead of `safe_load`.
- `read_yaml_file` also accepts a file-like object.


## [0.1.2](https://github.com/sdss/sdsstools/compare/0.1.1...0.1.2) - 2019-12-31

### Fixed

- The default target for the docs was pointing to `docs/sphinx/_build` instead of `docs/sphinx`.


## [0.1.1](https://github.com/sdss/sdsstools/compare/0.1.0...0.1.1) - 2019-12-31

### Added

- `sdss deploy` now also builds a wheel.
- `twine` and `wheel` dev dependencies for `sdss deploy`.
- Added a version of [releases](https://github.com/bitprophet/releases)

### Changed

- Bundle `toml` in `_vendor` instead of `pytoml`, which is deprecated.

## [0.1.0](https://github.com/sdss/sdsstools/releases/tag/0.1.0) - 2019-12-30

### Added

- Logging tools.
- Metadata and version finding tools.
- Command line interface (wrapper around tasks).
- Configuration tools.
