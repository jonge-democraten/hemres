from setuptools import setup

setup(
    name='hemres',
    version='0.3',
    packages=['hemres', 'hemres.migrations', 'hemres.templatetags'],
    url='http://github.com/jonge-democraten/hemres/',
    author='Jonge Democraten',
    author_email='ict@jongedemocraten.nl',
    description='Webapp for sending newsletters',
    include_package_data=True,
    license='MIT',
)
