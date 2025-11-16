from setuptools import find_packages, setup

setup(
    name="entry-point",
    version="0.1.dev0",
    description="Entry Point Test Fixture",
    author="Martijn Faassen",
    author_email="faassen@startifact.com",
    license="BSD",
    packages=find_packages(),
    zip_safe=False,
    install_requires=["morepath"],
    entry_points={"morepath": ["scan = entrypoint"]},
)
