#
from setuptools import find_packages, setup
setup(
    name='python_deriv_api',
    packages=find_packages(include=['deriv_api']),
    version='0.1.2',
    description='Python bindings for deriv.com websocket API',
    author='Deriv Group Services Ltd',
    author_email='learning+python@deriv.com',
    license='MIT',
    install_requires=['websockets==10.3', 'reactivex==4.0.*'],
    test_suite='tests',
    url='https://github.com/binary-com/python-deriv-api',
    project_urls={
        'Bug Tracker': "https://github.com/binary-com/python-deriv-api/issues",
        'Documentation': "https://binary-com.github.io/python-deriv-api",
        'Source Code': "https://github.com/binary-com/python-deriv-api",
        'Changelog': "https://github.com/binary-com/python-deriv-api/blob/master/CHANGELOG.md"
    },
    python_requires=">=3.9.6, !=3.9.7",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    long_description_content_type="text/markdown",
    long_description=open('README.md').read()
)
