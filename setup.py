'''Setup module for Rubin Observatory Argo Workflow dispatcher (Nublado).
'''
import codecs
import io
import os
import setuptools


def get_version(file, name='__version__'):
    '''Get the version of the package from the given file by
    executing it and extracting the given `name`.
    '''
    path = os.path.realpath(file)
    version_ns = {}
    with io.open(path, encoding="utf8") as f:
        exec(f.read(), {}, version_ns)
    return version_ns[name]


def local_read(filename):
    '''Convenience function for includes.
    '''
    full_filename = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        filename)
    return codecs.open(full_filename, 'r', 'utf-8').read()


NAME = 'wfdispatcher'
DESCRIPTION = 'REST server and client for managing Argo Workflows in Nublado'
LONG_DESCRIPTION = local_read("README.md")
VERSION = get_version('%s/_version.py' % NAME)
AUTHOR = 'Adam Thornton'
AUTHOR_EMAIL = 'athornton@lsst.org'
URL = 'https://github.com/sqre-lsst/wfdispatcher'
LICENSE = 'MIT'

setuptools.setup(
    name=NAME,
    version=get_version("%s/_version.py" % NAME),
    long_description=LONG_DESCRIPTION,
    packages=setuptools.find_packages(),
    url=URL,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    license=LICENSE,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 3.6',
        'License :: OSI Approved :: MIT License',
    ],
    keywords=['lsst', 'rubinobservatory', 'argo', 'workflow', 'jupyter'],
    install_requires=[
        'requests>=2.0.0,<3.0.0',
        'semver>=2.0.0,<3.0.0',
        'jupyterhubutils>=0.16.10,<1.0.0',
        'wsgiserver>=1.3,<2.0.0',
        'falcon>=2.0.0,<3.0.0',
        'python-jose[cryptography]>=3.1.0,<4.0.0',
    ],
    entry_points={
        'console_scripts': [
            'workflow-rest = wfdispatcher.server.standalone:standalone',
            'gen_data = wfdispatcher.helpers.standalone:standalone',
            'workflow-api-client = wfdispatcher.client.standalone:standalone',
        ],
    }
)
