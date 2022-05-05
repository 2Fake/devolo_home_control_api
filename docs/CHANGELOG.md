# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.18.2] - 2022/05/06

### Fixed

- Handle unreliable session refreshs more graceful

## [v0.18.1] - 2022/04/11

### Fixed

- Incorrect typehints

## [v0.18.0] - 2022/04/11

### Changed

- Drop Support for Python 3.6

### Fixed

- Ignore pending operation messages of HTTP devices

## [v0.17.4] - 2021/07/01

### Fixed

- Getting the version during runtime was broken
- Support websocket-client 1.1.0

## [v0.17.3] - 2021/04/09

### Fixed

- Session refresh with old websocket_client versions was not working

## [v0.17.2] - 2021/04/09

### Added

- Restored support for older websocket_client versions although not recommended to still use them

## [v0.17.1] - 2021/03/25

### Fixed

- Sometimes reconnecting the websocket failed

## [v0.17.0] - 2021/03/12

### Added

- Added devices are now added to the Publisher.
- Multilevel Async Settings are now updated via websocket

### Fixed

- websocket_client 0.58.0 support

## [v0.16.0] - 2020/11/07

### Added

- Removed devices are now announced via Publisher
- The gateway object contains the Z-Wave home_id

### Changed

- **BREAKING**: The siren now contains only a multi level switch to turn on a certain sound. The other properties moved to settings.
- **BREAKING**: Mydevolo is no longer a singleton

### Fixed

- Smart Groups are not ignored in all cases

## [v0.15.1] - 2020/10/13

### Fixed

- operationStatus messages were misinterpreted as new state
- pendingOperations of smart groups were misinterpreted as new values for devices

## [v0.15.0] - 2020/09/29

### Added

- Support for Eurotronic Spirit
- Shared zeroconf instances can now be used
- More units for multi level sensors
- Prevent switching of binary switches that have active remote switching protection
- Send changes of battery level to the subscribers

### Fixed

- Protection mode settings don't lead to websocket errors any more - [#65](https://github.com/2Fake/devolo_home_control_api/issues/65)

## [v0.14.0] - 2020/08/21

### Added

- Settings now update via websocket
- Last activity now updates via websocket
- Support for shutter movement as binary sensor
- Support for shutter overload warning as binary sensor
- Support for pending operations

### Changed

- **BREAKING**: Name and zone (also called room) moved into the general device settings property because they may change.

### Fixed

- Datetime objects are now in local time - [#59](https://github.com/2Fake/devolo_home_control_api/issues/59)

## [v0.13.0] - 2020/08/10

### Added

- Support for devolo Key-Fob
- Support for devolo Wall Switch

### Changed

- **BREAKING**: MildewProperty was reimplemented as BinarySensorProperty and DewpointProperty was reimplemented as MultiLevelSensorProperty.
- **BREAKING**: Devices attributes manID and manufacturerId, prodID and productId as well as prodTypeID and productTypeId were merged
to manufacturer_id, product_id and product_type_id respectively.

### Fixed

- Publisher sends consumption type additionally to element_uid and consumption value. - [#54](https://github.com/2Fake/devolo_home_control_api/issues/54)

## [v0.12.0] - 2020/06/09

### Added

- Support for devolo Siren

### Changed

- **BREAKING**: The naming of some setting properties changed

### Fixed

- Searching for devices now also works, if multiple devices have the same name.
- Websocket messages in unexpected format are handled gracefully.

## [v0.11.0] - 2020/05/26

### Added

- Support for devolo Radiator Thermostat
- Support for devolo Room Thermostat
- Support for devolo Dimmer FM
- Support for devolo Shutter FM
- Support for Danfoss Living Connect Z Radiator Thermostat
- Support for Danfoss Living Connect Z Room Thermostat
- Support for Qubino Flush Dimmer
- Support for Qubino Flush Shutter
- Multilevel sensor properties now have human readable units, if known

## [v0.10.0] - 2020/05/07

### Changed

- **BREAKING**: The method to set the state of a binary switch is now called "set"

### Fixed

- The websocket was closed after 30 minutes

## [v0.9.1] - 2020/04/27

### Fixed

- Fix package structure

## [v0.9.0] - 2020/04/27

### Changed

- **BREAKING**: Gateways being offline now throw a GatewayOfflineError
- Exceptions now have their own files

### Fixed

- Devices were always shown as offline
- Sometimes the websocket was closed before it was established
- Accessing an offline from the start gateway was not handled

## [v0.8.0] - 2020/04/20

### Added

- Support for Fibaro Floor Sensor
- Support for Fibaro Motion Sensor
- Support for Fibaro Smoke Sensor

### Changed

- **BREAKING**: We rethought the usage of Python properties and made some of them to regular methods.
- Z-Wave product information are filled with default values, if we cannot find the device in the database

## [v0.7.0] - 2020/04/16

### Added

- Support for devolo Door/Window Contact
- Support for devolo Flood Sensor
- Support for devolo Humidity Sensor
- Support for devolo Motion Sensor
- Support for devolo Smoke Detector

### Changed

- **BREAKING**: The properties don't have fetch methods any longer. Instead, the attributes are initially updated and should be used directly.

## [v0.6.4] - 2020/04/04

### Fixed

- Handle secure settings correctly

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
