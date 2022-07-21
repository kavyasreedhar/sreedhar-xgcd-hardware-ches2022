from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='xgcd',
    version='0.0.1',
    url='https://github.com/kavyasreedhar/sreedhar-xgcd-hardware-ches2022',
    author='Kavya Sreedhar',
    author_email='skavya@stanford.edu',
    packages=[
        "xgcd",
        "xgcd.functional_models",
        "xgcd.hardware",
        "xgcd.hardware.extended_gcd",
        "xgcd.hardware.jtag",
        "xgcd.hardware.jtag.genesis",
        "xgcd.utils",
        "xgcd.utils.tests_helper"
    ],
    install_requires=[
        "kratos==0.0.38",
        "magma-lang==2.2.26",
        "fault==3.1.2",
        "pytest==7.1.2",
        "mflowgen==0.4.0",
        "gnureadline==8.1.2"
    ],
    python_requires='>=3.7',
    long_description=long_description,
    long_description_content_type="text/markdown"
)
