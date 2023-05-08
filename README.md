# devolo Home Control API

[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/2Fake/devolo_home_control_api/pythonpackage.yml?branch=main)](https://github.com/2Fake/devolo_home_control_api/actions?query=workflow%3A%22Python+package%22)
[![PyPI - Downloads](https://img.shields.io/pypi/dd/devolo-home-control-api)](https://pypi.org/project/devolo-home-control-api/)
[![Code Climate maintainability](https://img.shields.io/codeclimate/maintainability/2Fake/devolo_home_control_api)](https://codeclimate.com/github/2Fake/devolo_home_control_api)
[![Coverage Status](https://coveralls.io/repos/github/2Fake/devolo_home_control_api/badge.svg?branch=main)](https://coveralls.io/github/2Fake/devolo_home_control_api?branch=main)

This project implements parts of the devolo Home Control API in Python. It is based on reverse engineering and therefore may fail with any new devolo update. If you discover a breakage, please feel free to [report an issue](https://github.com/2Fake/devolo_home_control_api/issues).

## System requirements

Defining the system requirements with exact versions typically is difficult. But there is a tested environment:

* Linux
* Python 3.7.12
* pip 22.0.1
* python-dateutil 2.8.2
* requests 2.27.1
* websocket_client 1.3.1
* zeroconf 0.38.4

Other versions and even other operating systems might work. Feel free to tell us about your experience. If you want to run our unit tests, you also need:

* pytest 7.2.2
* pytest-cov 4.0.0
* pytest-freezer 0.4.6
* requests-mock 3.10.0
* syrupy 4.0.0

## Versioning

In our versioning we follow [Semantic Versioning](https://semver.org/).

## Installing for usage

The Python Package Index takes care for you. Just use pip.

```bash
pip install devolo-home-control-api
```

## Installing for development

First, you need to get the sources.

```bash
git clone git@github.com:2Fake/devolo_home_control_api.git
```

Then you need to take care of the requirements.

```bash
cd devolo_home_control_api
python -m pip install .
```

If you want to run out tests, install the extra requirements and start pytest.

```bash
python -m pip install -e .[test]
pytest
```

## Quick start

To see that basic functionality, please look at our [small example](https://github.com/2Fake/devolo_home_control_api/blob/master/example.py). For this example, a working Home Control Central Unit must be attached to your my devolo account. After entering your my devolo username and password, simply run it:

```bash
python3 example.py
```

You will see changes to any BinarySwitch device (e.g. state or consumption) reported to your console. If the executing device is in the same LAN as the Home Control Central Unit, it will be discovered via Zeroconf. In this case, data will be collected from the Central Unit directly; otherwise data will be collected via cloud from my devolo.

### Connecting to my devolo

If you do not know your gateway ID, you can ask my devolo. For now, no other functionality is implemented, that you would need to access directly. If you discover other use cases, feel free to file a feature request.

```python
mydevolo = Mydevolo.get_instance()
mydevolo.user = "username"
mydevolo.password = "password"
for gateway_id in mydevolo.get_gateway_ids():
    print(gateway_id)
```

### Collecting Home Control data

There are two ways of getting data:

1. Let the websocket push data into your object, but still poll the object
1. Subscribe to the publisher and let it push (preferred)

#### Using websockets

When using websocket events, messages will keep the object up to date. Nevertheless, no further action is triggered. So you have to ask yourself. The following example will list the current state of all binary switches. If the state changes, you will not notice unless you ask again.

```python
homecontrol = HomeControl(gateway_id=gateway_id, mydevolo_instance=mydevolo)
for binary_switch in mprm.binary_switch_devices:
    for state in binary_switch.binary_switch_property:
        print (f"State of {binary_switch.name} ({binary_switch.binary_switch_property[state].element_uid}): {binary_switch.binary_switch_property[state].state}")
```

To execute this example, you again need a configured instance of Mydevolo.

#### Using subscriber

This preferred usage is shown in our [small example](https://github.com/2Fake/devolo_home_control_api/blob/master/example.py). On every websocket event, ```update()``` will be called. That way you can react to changes right away.

## Further usage

You will find snippets discribing other use cases in our [wiki](https://github.com/2Fake/devolo_home_control_api/wiki).
