import io
from setuptools import setup, find_packages

long_description = '\n'.join((
    io.open('README.rst', encoding='utf-8').read(),
    io.open('CHANGES.txt', encoding='utf-8').read()
))

setup(
    name='morepath',
    version='0.15.dev0',
    description="A micro web-framework with superpowers",
    long_description=long_description,
    author="Morepath developers",
    author_email="morepath@googlegroups.com",
    url='http://morepath.readthedocs.io',
    license="BSD",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Environment :: Web Environment',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Internet :: WWW/HTTP :: WSGI',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Development Status :: 5 - Production/Stable'
    ],
    keywords="web wsgi routing morepath",
    install_requires=[
        'setuptools',
        'webob >= 1.3.1',
        'reg >= 0.9.2',
        'dectate >= 0.10.1',
        'importscan',
    ],
    extras_require=dict(
        test=[
            'pytest >= 2.5.2',
            'py >= 1.4.20',
            'pytest-cov',
            'pytest-remove-stale-bytecode',
            'WebTest >= 2.0.14',
            'pyyaml',
        ],
    ),
)
