import os
from setuptools import setup, find_packages

setup(name='ns.real',
      version = '0.1.dev0',
      description="ns Test Fixture",
      author="Martijn Faassen",
      author_email="faassen@startifact.com",
      license="BSD",
      namespace_packages=['ns'],
      packages=find_packages(),
      zip_safe=False,
      install_requires=[
        'setuptools',
        'morepath'
        ]
      )
