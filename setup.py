from setuptools import find_packages, setup

long_description = "\n".join(
    (
        open("README.rst", encoding="utf-8").read(),
        open("CHANGES.txt", encoding="utf-8").read(),
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
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
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
            "pytest >= 7",
            "pytest-remove-stale-bytecode",
            "WebTest >= 2.0.14",
        ],
        pep8=["black", "flake8", "isort"],
        coverage=["pytest-cov"],
        docs=["sphinx", "pyyaml", "WebTest >= 2.0.14"],
    ),
)
