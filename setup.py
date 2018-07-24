import os
from setuptools import setup


def read(file_name):
    with open(os.path.join(os.path.dirname(__file__), file_name)) as f:
        return f.read()


setup(
    name="saltnanny",
    version="0.3.0",
    author="Dun and Bradstreet Inc.",
    author_email="devops@dandb.com",
    description='Python Module that parses salt returns stored in an external job cache and logs output',
    license="GPLv3",
    keywords="Salt SaltStack Redis redis_return parse cache external",
    url="https://github.com/dandb/salt-nanny",
    packages=['saltnanny'],
    entry_points={
        'console_scripts': [
            'salt-nanny = saltnanny.salt_nanny_tool:main'
        ]
    },
    include_package_data=True,
    install_requires=[
        'redis>=2.0.0',
    ],
    extras_require={'test': [
        'coverage',
        'mock>=2.0.0',
        'fakeredis>=0.7.0',
        'pytest',
    ]},
    long_description=read('README.rst')
)
