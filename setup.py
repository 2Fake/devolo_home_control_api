import shlex
from subprocess import check_call

from setuptools import find_packages, setup
from setuptools.command.develop import develop

with open("README.md", "r") as fh:
    long_description = fh.read()


# Create post develop command class for hooking into the python setup process
# This command will run after dependencies are installed
class PostDevelopCommand(develop):

    def run(self):
        try:
            check_call(shlex.split("pre-commit install"))
        except Exception:
            print("Unable to run 'pre-commit install'")
        develop.run(self)


setup(
    name="devolo_home_control_api",
    use_scm_version=True,
    author="Markus Bong, Guido Schmitz",
    author_email="m.bong@famabo.de, guido.schmitz@fedaix.de",
    description="devolo Home Control API in Python",
    license="GPLv3",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/2Fake/devolo_home_control_api",
    packages=find_packages(exclude=("tests*",
                                    )),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "importlib-metadata;python_version<'3.8'",
        "requests",
        "websocket_client>=0.58.0",
        "zeroconf",
    ],
    setup_requires=["setuptools_scm"],
    extras_require={
        "dev": [
            "pre-commit",
        ],
        "test": [
            "pytest",
            "pytest-cov",
            "pytest-mock",
        ],
    },
    cmdclass={"develop": PostDevelopCommand},
    python_requires=">=3.6",
)
