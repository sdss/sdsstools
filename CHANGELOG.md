# Changelog

## [Unreleased](https://github.com/sdss/sdsstools/compare/0.1.1...HEAD)

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
