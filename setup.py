from setuptools import setup

setup(
    name='hemres',
    version='0.7',
    packages=['hemres', 'hemres.migrations', 'hemres.templatetags'],
    url='http://github.com/jonge-democraten/hemres/',
    author='Jonge Democraten',
    author_email='ict@jongedemocraten.nl',
    description='Webapp for sending newsletters',
    include_package_data=True,
    install_requires=['html2text>=2015.6.21', 'bleach>=1.4.2', 'django-rq>=0.8.0', 'inlinestyler>=0.2.1', 'future>=0.15.2'],
    license='MIT',
)
