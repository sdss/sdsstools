# Changelog

## [Unreleased](https://github.com/sdss/sdsstools/compare/0.1.5...HEAD)

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
