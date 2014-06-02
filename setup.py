# -*- coding: utf-8 -*-
"""
This module contains the tool of acsone.recipe.odoo.pydev
"""
import os
from setuptools import setup, find_packages


def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

version = '1.0'

long_description = (
    read('README.rst')
    #+ '\n' +
    #'Detailed Documentation\n'
    #'**********************\n'
    #+ '\n' +
    #read('acsone', 'recipe', 'odoo', 'pydev', 'README.txt')
    + '\n' +
    'Contributors\n'
    '************\n'
    + '\n' +
    read('CONTRIBUTORS.txt')
    + '\n' +
    'Change history\n'
    '**************\n'
    + '\n' +
    read('CHANGES.txt')
    + '\n' +
   'Download\n'
    '********\n')

entry_point = 'acsone.recipe.odoo.pydev:Recipe'
entry_points = {"zc.buildout": ["default = %s" % entry_point]}

requires = ['setuptools', 'zc.buildout', 'anybox.recipe.openerp', 'collective.recipe.omelette', ]
tests_require = requires + ['nose', 'bzr', 'anybox.recipe.openerp[bzr]', 'zope.testing', 'manuel'],

setup(name='acsone.recipe.odoo.pydev',
      version=version,
      description="A buildout recipe to install and configure a PyDev project for Openerp",
      long_description=long_description,
      # Get more strings from
      # http://pypi.python.org/pypi?:action=list_classifiers
      classifiers=[
        'Framework :: Buildout :: Recipe',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU Affero General Public License v3 or '
        'later (AGPLv3+)',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Software Development :: Libraries :: Python Modules',
        ],
      keywords='',
      author='ACSONE SA/NV',
      author_email='laurent.mignon__at__acsone.eu',
      url='http://pypi.python.org/pypi/acsone.recipe.odoo.pydev',
      license='GPLv3+',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['acsone', 'acsone.recipe', 'acsone.recipe.odoo'],
      include_package_data=True,
      data_files=[('', ['CHANGES.txt', 'CONTRIBUTORS.txt'])],
      zip_safe=False,
      install_requires=requires,
      tests_require=tests_require,
      extras_require = {
        'tests': tests_require,
        'bzr' : ['anybox.recipe.openerp[bzr]'],
      },
      test_suite='acsone.recipe.odoo.pydev.tests.test_docs.test_suite',
      entry_points=entry_points,
      )
