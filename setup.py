from setuptools import setup, find_packages
import os

version = '0.1.0'

requires = [
    'setuptools',
]

databridge_requires = requires + [
    'PyYAML',
    'gevent',
    'redis',
    'LazyDB',
    'ExtendedJournalHandler',
    'requests',
    'openprocurement_client>=1.0b2'
]

api_requires = requires + [
    'openprocurement.api>=2.3',
    'barbecue',
    'chaussette',
    'cornice',
    'couchdb-schematics',
    'gevent',
    'iso8601',
    'jsonpatch',
    'libnacl',
    'pbkdf2',
    'pycrypto',
    'pyramid_exclog',
    'requests',
    'rfc6266',
    'setuptools',
    'tzlocal'
]

test_requires = api_requires + requires + [
    'webtest',
    'python-coveralls',
    'bottle'
]

entry_points = {
    'console_scripts': [
        'integrations_edr_data_bridge = openprocurement.integrations.edr.databridge:main'
    ],
    'paste.app_factory': [
        'main = openprocurement.integrations.edr:main'
    ],
}

setup(name='openprocurement.integrations.edr',
      version=version,
      description="openprocurement.integrations.edr",
      long_description=open("README.rst").read(),
      classifiers=[
        "Framework :: Pylons",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application"
        ],
      keywords="web services",
      author='Quintagroup, Ltd.',
      author_email='info@quintagroup.com',
      license='Apache License 2.0',
      url='https://github.com/Krokop/openprocurement.integrations.edr',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['openprocurement', 'openprocurement.integrations'],
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=test_requires,
      extras_require={'databridge': databridge_requires,
                      'test': test_requires,
                      'api': api_requires},
      entry_points=entry_points)
