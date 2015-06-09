import os
from setuptools import setup, find_packages

setup(name='no_mp_sub',
      version = '0.1.dev0',
      description="No Mp Sub Test Fixture",
      author="Martijn Faassen",
      author_email="faassen@startifact.com",
      license="BSD",
      packages=find_packages(),
      zip_safe=False,
      install_requires=[
        'no-mp',
        ]
      )
