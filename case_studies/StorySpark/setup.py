# setup.py
from setuptools import setup, find_packages

setup(
    name="storyspark",
    version="0.1.0",
    description="StorySpark backend modules",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        # any runtime deps, e.g. "azure-functions", "requests"
    ],
)