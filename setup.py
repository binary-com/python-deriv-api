#
from setuptools import find_packages, setup
setup(
    name='python_deriv_api',
    packages=find_packages(include=['deriv_api']),
    version='0.1.0',
    description='Python bindings for deriv.com websocket API',
    author='deriv.com',
    author_email='',
    license='MIT',
    install_requires=['websockets==9.1', 'asyncio==3.4.3', 'rx==3.1.1'],
    test_suite='tests',
    url='https://github.com/binary-com/python-deriv-api',
    project_urls={
        'Bug Tracker': "https://github.com/binary-com/python-deriv-api/issues"
    },
    python_requires="==3.9.6",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ]
)
