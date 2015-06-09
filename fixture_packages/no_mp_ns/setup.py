import os
from setuptools import setup, find_packages

setup(name='no_mp_ns',
      version = '0.1.dev0',
      description="No Morepath NS Test Fixture",
      author="Martijn Faassen",
      author_email="faassen@startifact.com",
      license="BSD",
      namespace_packages=['ns'],
      packages=find_packages(),
      zip_safe=False,
      install_requires=[
        'setuptools',
        ]
      )
