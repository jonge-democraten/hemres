from setuptools import setup, find_packages

setup(
    name='hemres',
    version='0.18',
    description='Newsletter module for Jonge Democraten websites',
    packages=find_packages(),
    url='http://github.com/jonge-democraten/hemres/',
    author='Jonge Democraten',
    include_package_data=True,
    license='MIT',
    install_requires=['bleach>=1.5','filelock>=2.0'],
)
