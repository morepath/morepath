import os
from setuptools import setup, find_packages

setup(name='under_score',
      version = '0.1.dev0',
      description="Project name with under scores",
      author="Martijn Faassen",
      author_email="faassen@startifact.com",
      license="BSD",
      packages=find_packages(),
      zip_safe=False,
      install_requires=[
        'setuptools',
        'morepath'
        ]
      )
