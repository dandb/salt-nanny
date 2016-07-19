#!/usr/bin/env python

import os
from setuptools import setup
from pip.req import parse_requirements


def read(file_name):
    return open(os.path.join(os.path.dirname(__file__), file_name)).read()


def get_required_modules(file_name):
    modules_with_versions = parse_requirements(file_name, session=False)
    return [str(module.req) for module in modules_with_versions]

setup(
    name="saltnanny",
    version="0.1.2",
    author="Dun and Bradstreet Inc.",
    author_email="devops@dandb.com",
    description='Python Module that parses salt returns stored in an external job cache and logs output',
    license="GPLv3",
    keywords="Salt SaltStack Redis redis_return parse cache external",
    url="https://github.com/dandb/saltnanny",
    packages=['saltnanny'],
    include_package_data=True,
    cmdclass={},
    install_requires=get_required_modules('requirements.txt'),
    tests_require=get_required_modules('tests/requirements.txt'),
    test_suite="nose.collector",
    long_description=read('README.md')
)
