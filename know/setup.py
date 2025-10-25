#!/usr/bin/env python3
"""
Setup script for Know Tool
Enables installation via pip
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text() if (this_directory / "README.md").exists() else ""

setup(
    name="know-tool",
    version="1.0.0",
    author="LB Project",
    description="High-performance specification graph management tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourproject/know",
    packages=find_packages(exclude=["tests", "tests.*"]),
    py_modules=["know_minimal"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Systems Administration",
    ],
    python_requires=">=3.8",
    install_requires=[
        "click>=8.0",
        "rich>=13.0",
    ],
    extras_require={
        "full": [
            "pydantic>=2.0",
            "networkx>=3.0",
            "aiofiles>=0.8",
            "python-dotenv>=0.19",
        ],
        "dev": [
            "pytest>=7.0",
            "pytest-asyncio>=0.21",
            "pytest-cov>=4.0",
            "black>=23.0",
            "mypy>=1.0",
            "pylint>=2.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "know=know:cli",
        ],
    },
    include_package_data=True,
    package_data={
        "know_lib": ["../config/*.json"],
    },
)