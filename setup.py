#!/usr/bin/env python

import os
import re
from setuptools import setup


def read(file_name):
    with open(os.path.join(os.path.dirname(__file__), file_name)) as f:
        return f.read()


def get_required_modules(file_name):
    module_list = read(file_name).split()
    return map(lambda x: re.split('==|>=|>|<', x)[0], module_list)

setup(
    name="saltnanny",
    version="0.2.3",
    author="Dun and Bradstreet Inc.",
    author_email="devops@dandb.com",
    description='Python Module that parses salt returns stored in an external job cache and logs output',
    license="GPLv3",
    keywords="Salt SaltStack Redis redis_return parse cache external",
    url="https://github.com/dandb/salt-nanny",
    packages=['saltnanny'],
    scripts=['salt-nanny'],
    include_package_data=True,
    cmdclass={},
    install_requires=get_required_modules('requirements.txt'),
    tests_require=get_required_modules('tests/requirements.txt'),
    test_suite="nose.collector",
    long_description=read('README.rst') + '\n\n' + read('CHANGES')
)
