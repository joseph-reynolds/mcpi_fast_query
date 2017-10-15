#!/usr/bin/python3

"""A fast batch query function for Minecraft Pi edition."""

import io
import os
import sys
from setuptools import setup, find_packages

if sys.version_info[0] == 2:
    if not sys.version_info >= (2, 7):
        raise ValueError('This package requires Python 2.7 or newer')
elif sys.version_info[0] == 3:
    if not sys.version_info >= (3, 4):
        raise ValueError('This package requires Python 3.4 or newer')
else:
    raise ValueError('Unrecognized major version of Python')

package_dir = os.path.abspath(os.path.dirname(__file__))


__project__      = 'mcpi_fast_query'
__version__      = '0.1.0'
__author__       = 'Joseph Reynolds'
__author_email__ = 'joseph-reynolds@charter.net'
__url__          = 'http://github.com/joseph-reynolds/mcpi_fast_query'
__platforms__    = 'ALL'

__classifiers__ = [
    'Development Status :: 3 - Alpha',
    'Environment :: Console',
    'Environment :: X11 Applications',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: BSD License',
    'Operating System :: POSIX :: Linux',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3.4',
    'Topic :: Games/Entertainment',
    ]

__keywords__ = [
    'raspberrypi',
    'minecraft',
    ]

__requires__ = [
    'picraft',
    ]

__extra_requires__ = {
    }

__entry_points__ = {
    }


def main():
    
    with io.open(os.path.join(package_dir, 'README.rst'), 'r') as readme:
        long_description = readme.read()
        
    setup(
        name                 = __project__,
        version              = __version__,
        description          = __doc__,
        long_description     = long_description,
        classifiers          = __classifiers__,
        author               = __author__,
        author_email         = __author_email__,
        url                  = __url__,
        license              = [
            c.rsplit('::', 1)[1].strip()
            for c in __classifiers__
            if c.startswith('License ::')
            ][0],
        keywords             = __keywords__,
        packages             = find_packages(),
        include_package_data = False,
        platforms            = __platforms__,
        install_requires     = __requires__,
        extras_require       = __extra_requires__,
        entry_points         = __entry_points__,
        )


if __name__ == '__main__':
    main()

