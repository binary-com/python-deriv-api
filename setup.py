#
from setuptools import find_packages, setup
setup(
    name='deriv_api',
    packages=find_packages(include=['deriv_api']),
    version='0.1.0',
    description='Deriv API',
    author='deriv.com',
    license='MIT',
    install_requires=['websockets==9.1', 'asyncio==3.4.3', 'rx==3.1.1'],
    setup_requires=['pytest-runner==5.3.1'],
    tests_require=['pytest==6.2.5'],
    test_suite='tests',
)
