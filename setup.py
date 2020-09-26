from setuptools import find_packages, setup

setup(
    name="smol",
    version="0.1.0",
    url="https://github.com/thinkofher/smol",
    author="Beniamin Dudek",
    author_email="beniamin.dudek@yahoo.com",
    description="Small and lean framework for automated tests.",
    packages=find_packages(),
    install_requires=['attrs==20.2.0'],
)
