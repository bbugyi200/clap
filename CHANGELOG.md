# Changelog for `clap`

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog], and this project adheres to
[Semantic Versioning].

[Keep a Changelog]: https://keepachangelog.com/en/1.0.0/
[Semantic Versioning]: https://semver.org/


## [Unreleased](https://github.com/bbugyi200/clap/compare/0.3.1...HEAD)

No notable changes have been made.


## [0.3.1](https://github.com/bbugyi200/clap/compare/0.3.0...0.3.1) - 2021-12-20

### Fixed

* Fix breaking changes from `bugyi.lib==0.11` and update requirements.

### Miscellaneous

* Migrate from `pylogutils` to `python-logrus` dependency.


## [0.3.0](https://github.com/bbugyi200/clap/compare/0.2.2...0.3.0) - 2021-12-20

### Added

* New `comma_list_or_file` helper class for parsing comma-separated CLI args.

### Removed

* *BREAKING CHANGE*: Sync with cc-python version `v2021.12.20` (drops Python3.7 support).


## [0.2.2](https://github.com/bbugyi200/clap/compare/0.2.1...0.2.2) - 2021-09-28

### Fixed

* Fix `--version` option.


## [0.2.1](https://github.com/bbugyi200/clap/compare/0.2.0...0.2.1) - 2021-09-26

### Fixed

* Added `importlib-metadata` package as direct dependency of this package.


## [0.2.0](https://github.com/bbugyi200/clap/compare/0.1.0...0.2.0) - 2021-09-26

### Added

* Copied code from `bugyi.lib.cli` module.


## [0.1.0](https://github.com/bbugyi200/clap/releases/tag/0.1.0) - 2021-09-26

### Miscellaneous

* First release.
