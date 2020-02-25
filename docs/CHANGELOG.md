# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

- React to a new/deleted device

## [v0.3.0] - 2020/02/21

### Added

- Support for Fibaro Double Relay Switch
- Lookup for Z-Wave device information
- React on device online state

### Changed

- **BREAKING**: The relation between the objects changed completely.

## [v0.2.0] - 2020/02/05

### Added

- Lookup methods, if UIDs are unknown
- React on maintenance mode of mydevolo
- Handle offline gateways
- Handle offline devices

### Changed

- Publisher now returns a list of element_uid and value
- Rename MprmDeviceError to MprmDeviceCommunicationError

## [v0.1.0] - 2020/01/31

### Added

- Support for devolo Metering Plug v1
- Support for devolo Metering Plug v2
- Support for devolo Switch FM
- Support for Qubino Flush 1 Relay
- Support for Qubino Flush 1D Relay
- Support for Fibaro Wall Plug
