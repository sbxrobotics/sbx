#!/usr/bin/env python

"""sbx setup."""

from setuptools import setup, find_packages

with open("README.md") as readme_filehandle:
    readme_str = readme_filehandle.read()

with open("requirements.txt") as requirements_filehandle:
    requirements_str = requirements_filehandle.read().splitlines()
    
setup(
    name="sbx",
    version="0.0.1",
    description="A CLI for interacting with the SBX Robotics API.",
    long_description=readme_str,
    long_description_content_type="text/markdown",
    author="SBX Robotics Inc.",
    author_email="info@sbxrobotics.com",
    url="https://github.com/sbxrobotics/sbx/",
    packages=["sbx"],
    package_dir={"sbx": "sbx"},
    package_data={"sbx": ["py.typed"]},
    entry_points={
        "console_scripts": [
            "sbx=sbx.cli.cli:cli",
        ]
    },
    include_package_data=True,
    install_requires=requirements_str,
    license="MIT license",
    zip_safe=False,
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Environment :: Console",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    # TODO: (T2522) Add tests for profit and glory
    # test_suite="tests",
    # tests_require=test_requirements,
)