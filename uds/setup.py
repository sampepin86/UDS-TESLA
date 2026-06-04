"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

import codecs
import os
import setuptools
from setuptools.command.test import test as TestCommand
import re

__author__ = 'eprasetio'
__email__ = 'eprasetio@teslamotors.com'


class RobotframeworkTestCommand(TestCommand):
    '''
    This is a class definition for a module that uses robotframework to implement unit tests. Other classes
    could be defined following this template for various other testing frameworks, e.g. nose, unittest, pytest, etc.
    '''
    import sys
    callstring = [sys.executable,
                  '-m',
                  'robot.run',
                  '--loglevel',
                  'TRACE:INFO',
                  '--noncritical',
                  'in_development',
                  '--noncritical',
                  'not_implemented',
                  'ModuleTests']

    def initialize_options(self):
        TestCommand.initialize_options(self)

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # TODO: Implement some robot framework tests.
        pass
        # import subprocess
        # import os
        # return_code = subprocess.call(args=self.callstring, env=os.environ.copy(), cwd="tests")
        # raise SystemExit(return_code)

# Get the long description from the relevant file
here = os.path.abspath(os.path.dirname(__file__))
with codecs.open('README.md', encoding='utf-8') as f:
    long_description = f.read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

PACKAGE_NAME = "uds"
tests_require = ['robotframework', 'virtualenv', 'prospector'] # Your test requirements here

if __name__ == "__main__":
    """
    BEGIN: DO NOT MODIFY
    The following lines allow for automatic versioning by Jenkins. Do not modify them!

    The third number in the version triple of all jenkins-managed modules will always be the jenkins build number.
    The first two numbers can be modified by changing the variable "major_version" of the "update_version.py" file.

    For more info, see how jenkins builds this project at: sysval-jenkins.teslamotors.com
    """

    VERSION_FILE = os.path.join("source", PACKAGE_NAME, "_version.py")
    with open(VERSION_FILE) as vf:
        lines = vf.read()
    version_regex = "^__version__ = ['\"]([^'\"]*)['\"]"
    search_result = re.search(version_regex, lines, re.M)
    __version__ = None
    if search_result:
        __version__ = search_result.group(1)
    else:
        raise RuntimeError("Unable to find version string in %s." % (VERSION_FILE,))

    """ END: DO NOT MODIFY """
    
    setuptools.setup(
        name=PACKAGE_NAME,
        cmdclass={'test': RobotframeworkTestCommand},  # Note: use your specific test framework's TestCommand class here

        # Versions should comply with PEP440.  For a discussion on single-sourcing
        # the version across setup.py and the project code, see
        # https://packaging.python.org/en/latest/single_source_version.html
        version=__version__,

        description='A package exposing UDS functionality to Python',
        long_description=long_description,

        # The project's main homepage.
        url='https://stash.teslamotors.com/projects/VAL/infrastructure/UDS',

        # Author details
        author=__author__,
        author_email=__email__,


        # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
        classifiers=[
            # How mature is this project? Common values are
            #   1 - Planning
            #   3 - Alpha
            #   4 - Beta
            #   5 - Production/Stable
            'Development Status :: 3 - Alpha',

            # Indicate who your project is intended for
            'Intended Audience :: Testers',
            'Topic :: Software Development :: Testing',
            'Topic :: Software Development :: Quality Assurance',

            # Specify the Python versions you support here. In particular, ensure
            # that you indicate whether you support Python 2, Python 3 or both.
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 2.6',
            'Programming Language :: Python :: 2.7',
        ],

        # What does your project relate to?
        keywords="validation infrastructure uds",

        # You can just specify the packages manually here if your project is
        # simple. Or you can use find_packages().
        # In the case of this repo. We aren't installing anyting but the pre-requisites
        # But if you want any packages to be installed here, use the following example as a guide:
        # packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
        package_dir={'': 'source'},
        packages=setuptools.find_packages('source'),

        # List any additional sources that should be included when searching for dependencies
        # https://pythonhosted.org/setuptools/setuptools.html#declaring-extras-optional-features-with-their-own-dependencies
        # Here is an example of how to do this:
        #dependency_links=["https://artifactory.dev.teslamotors.com/artifactory/"],

        # List run-time dependencies here.  These will be installed by pip when
        # your project is installed. For an analysis of "install_requires" vs pip's
        # requirements files see:
        # https://packaging.python.org/en/latest/requirements.html
        dependency_links=["https://pypi.python.org/simple/"],
        install_requires=requirements,
        tests_require=tests_require,

        # List additional groups of dependencies here (e.g. development or test
        # dependencies). You can install these using the following syntax,
        # for example:
        # $ pip install -e .[dev,test]
        extras_require={
            'dev': [],
            'test': tests_require,
        },

        # If there are data files included in your packages that need to be
        # installed, specify them here.  If using Python 2.6 or less, then these
        # have to be included in MANIFEST.in as well.
        package_data={
            'uds':['**/*.*'],
        },
        include_package_data=True,
        # Although 'package_data' is the preferred approach, in some case you may
        # need to place data files outside of your packages. See:
        # http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files # noqa
        # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
        # data_files=[('my_data', ['data/data_file'])],

        # To provide executable scripts, use entry points in preference to the
        # "scripts" keyword. Entry points provide cross-platform support and allow
        # pip to create the appropriate form of executable for the target platform.
        # entry_points={
        #     'console_scripts': [
        #         'sample=sample:main',
        #     ],
        # },
    )