"""
Alternative Credit Scoring System for SMEs
==========================================

A machine learning system that predicts loan repayment probability for small businesses
using non-traditional data sources, with focus on African/Nigerian markets.
"""

from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="alternative-credit-scoring",
    version="0.1.0",
    description="ML system for SME credit scoring using alternative data",
    author="Credit Scoring Team",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=requirements,
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
)
