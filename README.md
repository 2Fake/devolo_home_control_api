# devolo_home_control_api

[![GitHub Workflow Status](https://img.shields.io/github/workflow/status/2Fake/devolo_home_control_api/Python%20package)](https://github.com/2Fake/devolo_home_control_api/actions?query=workflow%3A%22Python+package%22)
[![PyPI - Downloads](https://img.shields.io/pypi/dd/devolo-home-control-api)](https://pypi.org/project/devolo-home-control-api/)
[![Libraries.io SourceRank](https://img.shields.io/librariesio/sourcerank/pypi/devolo-home-control-api)](https://libraries.io/pypi/devolo-home-control-api)
[![Code Climate maintainability](https://img.shields.io/codeclimate/maintainability/2Fake/devolo_home_control_api)](https://codeclimate.com/github/2Fake/devolo_home_control_api)
[![Coverage Status](https://coveralls.io/repos/github/2Fake/devolo_home_control_api/badge.svg?branch=master)](https://coveralls.io/github/2Fake/devolo_home_control_api?branch=master)

This project implements parts of the devolo Home Control API in Python. It is based on reverse engineering and therefore may fail with any new devolo update. If you discover a breakage, please feel free to [report an issue](https://github.com/2Fake/devolo_home_control_api/issues).

## System requirements

Defining the system requirements with exact versions typically is difficult. But there is a tested environment:

* Linux
* Python 3.6.9
* pip 18.1
* requests 2.22.0
* websocket_client 0.56.0
* zeroconf 0.24.4

Other versions and even other operating systems might work. Feel free to tell us about your experience. If you want to run our unit tests, you also need:

* pytest 4.5.0
* pytest-mock 1.11.2

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
python setup.py install
```

If you want to run out tests, change to the tests directory and start pytest via setup.py.

```bash
python setup.py test
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
for gateway_id in mydevolo.gateway_ids:
    print(gateway_id)
```

### Collecting Home Control data

There are two ways of getting data:

1. Let the websocket push data into your object, but still poll the object
1. Subscribe to the publisher and let it push (preferred)

#### Using websockets

When using websocket events, messages will keep the object up to date. Nevertheless, no further action is triggered. So you have to ask yourself. The following example will list the current state of all binary switches. If the state changes, you will not notice unless you ask again.

```python
homecontrol = HomeControl(gateway_id=gateway_id)
for binary_switch in mprm.binary_switch_devices:
    for state in binary_switch.binary_switch_property:
        print (f"State of {binary_switch.name} ({binary_switch.binary_switch_property[state].element_uid}): {binary_switch.binary_switch_property[state].state}")
```

To execute this example, you again need a configured instance of Mydevolo.

#### Using subscriber

This preferred usage is shown in our [small example](https://github.com/2Fake/devolo_home_control_api/blob/master/example.py). On every websocket event, ```update()``` will be called. That way you can react to changes right away.
