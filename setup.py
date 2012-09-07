#!/usr/bin/env python


from setuptools import setup

setup(
    name='AcousticModem',
    version='1.0',

    author='Hamilton Kibbe',
    author_email='hamilton.kibbe@gmail.com',

    maintainer='Hamilton Kibbe',
    maintainer_email='hamilton.kibbe@gmail.com',
    install_requires=['pyserial'], 

    description='Python interface to Teledyne Benthos Acoustic modems',
    url='http://github.com/hamiltonkibbe/AcousticModem',
    packages=['AcousticModem']
)