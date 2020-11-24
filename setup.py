import shlex
from subprocess import check_call

from setuptools import find_packages, setup
from setuptools.command.develop import develop

from devolo_home_control_api import __version__

with open("README.md", "r") as fh:
    long_description = fh.read()


# Create post develop command class for hooking into the python setup process
# This command will run after dependencies are installed
class PostDevelopCommand(develop):

    def run(self):
        try:
            check_call(shlex.split("pre-commit install"))
        except Exception as e:
            print("Unable to run 'pre-commit install'")
        develop.run(self)


setup(
    name="devolo_home_control_api",
    version=__version__,
    author="Markus Bong, Guido Schmitz",
    author_email="m.bong@famabo.de, guido.schmitz@fedaix.de",
    description="devolo Home Control API in Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/2Fake/devolo_home_control_api",
    packages=find_packages(exclude=("tests*")),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "requests",
        "websocket_client",
        "zeroconf",
    ],
    extras_require={
        "dev": [
            "pre-commit",
        ],
        "test": [
            "pytest",
            "pytest-cov",
            "pytest-mock",
        ],
        "dev": ["pre-commit"],
    },
    cmdclass={"develop": PostDevelopCommand},
    python_requires=">=3.6",
)
