import re
from setuptools import setup, find_packages

with open('requirements.txt') as requirements_file:
    install_requirements = requirements_file.read().splitlines()

setup(
    name        = "sync-s3-bucket-configurations",
    version     = "0.0.0",
    description = "sync-s3-bucket-configurations",
    author      = "suzuki-navi",
    packages    = find_packages(),
    install_requires = install_requirements,
    include_package_data = True,
    entry_points = {
        "console_scripts": [
            "sync-s3-bucket-configurations = sync_s3_bucket_configurations.main:main",
        ]
    },
)

