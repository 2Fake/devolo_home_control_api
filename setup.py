import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="devolo_home_control_api",
    version="0.7.0",
    author="Markus Bong, Guido Schmitz",
    author_email="m.bong@famabo.de, guido.schmitz@fedaix.de",
    description="devolo Home Control API in Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/2Fake/devolo_home_control_api",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "requests",
        "websocket_client<=0.56.0",
        "zeroconf"
    ],
    setup_requires=[
        "pytest-runner"
    ],
    tests_require=[
        "pytest",
        "pytest-cov",
        "pytest-mock<2"
    ],
    python_requires='>=3.6',
)
