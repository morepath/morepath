from setuptools import find_namespace_packages, setup

setup(
    name="ns.real2",
    version="0.1.dev0",
    description="ns2 Test Fixture",
    author="Martijn Faassen",
    author_email="faassen@startifact.com",
    license="BSD",
    namespace_packages=["ns"],
    packages=find_namespace_packages(),
    zip_safe=False,
    install_requires=["morepath"],
)
