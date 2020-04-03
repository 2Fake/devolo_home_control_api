# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Support for devolo Door/Window Contact
- Support for devolo Flood Sensor
- Support for devolo Humidity Sensor
- Support for devolo Motion Sensor
- Support for devolo Smoke Detector

### Changed

- **BREAKING**: The properties don't have fetch methods any longer. Instead, the attribute are initially updated and should be used directly.

## [v0.6.3] - 2020/03/30

### Fixed

- Handle secure included devices correctly

## [v0.6.2] - 2020/03/19

### Changed

- Add install_requires to setup.py

### Fixed

- Correct websocket log message event on close

## [v0.6.1] - 2020/03/19

### Changed

- Small adjustments when closing the websocket. This is just needed for Home Assistant.

## [v0.6.0] - 2020/03/18

### Added

- with-statement can be used to properly terminate the websocket

### Changed

- The inheritance of objects changed. This should not brake anything.

### Fixed

- Correct state of a device, if device was offline during communication

## [v0.5.0] - 2020/03/03

### Changed

- Speed up device collection

### Fixed

- Catch error if a smart group is switched

## [v0.4.0] - 2020/02/27

### Added

- React to a new/deleted device

### Fixed

- Fix crash if setting_uid is None

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
