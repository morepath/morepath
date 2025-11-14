from setuptools import find_packages, setup

setup(
    name="base",
    version="0.1.dev0",
    description="Base Test Fixture",
    author="Martijn Faassen",
    author_email="faassen@startifact.com",
    license="BSD",
    packages=find_packages(),
    zip_safe=False,
    install_requires=["setuptools", "morepath"],
)
