import os
import sys

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = """por.models
=============

for more details visit: http://getpenelope.github.com/"""
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'SQLAlchemy',
    'zope.sqlalchemy',
    'psycopg2',
    'plone.i18n',
    'transaction',
    'PasteScript',
    'lorem-ipsum-generator',
    'Trac',
    'profilehooks',
    'por.dashboard'
    ]

if sys.version_info[:3] < (2, 5, 0):
    requires.append('pysqlite')

setup(name='por.models',
      version='1.3.9',
      description='Tempi progetti',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      keywords='web wsgi bfg pylons pyramid',
      namespace_packages=['por'],
      author='Penelope Team',
      author_email='penelopedev@redturtle.it',
      url='https://getpenelope.github.com',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      test_suite='por.models.tests',
      entry_points="""\
      [console_scripts]
      populate_penelope = por.models.scripts.populate:main
      populate_with_dummies = por.models.scripts.dummies:main
      import_svn = por.models.scripts.importsvn:main
      """,
      )
