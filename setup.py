import io
from setuptools import setup, find_packages

long_description = "\n".join(
    (
        io.open("README.rst", encoding="utf-8").read(),
        io.open("CHANGES.txt", encoding="utf-8").read(),
    )
)

setup(
    name="morepath",
    version="0.20.dev0",
    description="A micro web-framework with superpowers",
    long_description=long_description,
    author="Morepath developers",
    author_email="morepath@googlegroups.com",
    url="https://morepath.readthedocs.io",
    license="BSD",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Environment :: Web Environment",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Internet :: WWW/HTTP :: WSGI",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Development Status :: 5 - Production/Stable",
    ],
    keywords="web wsgi routing morepath",
    python_requires=">=3.6",
    install_requires=[
        "setuptools",
        "webob >= 1.7.0",
        "reg >= 0.12",
        "dectate >= 0.14",
        "importscan >= 0.2",
    ],
    extras_require=dict(
        test=[
            "pytest >= 2.9.0",
            "pytest-remove-stale-bytecode",
            "WebTest >= 2.0.14",
        ],
        pep8=["flake8", "black"],
        coverage=["pytest-cov"],
        docs=["sphinx", "pyyaml", "WebTest >= 2.0.14"],
    ),
)
