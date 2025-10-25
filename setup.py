"""
Setup script for HealthSync project.
Installs dependencies and prepares the environment.
"""

from setuptools import setup, find_packages

with open("requirements.txt", "r") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="healthsync",
    version="1.0.0",
    author="HealthSync Team",
    author_email="team@healthsync.ai",
    description="Decentralized healthcare data exchange system using ASI Alliance technologies",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/healthsync/healthsync",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Healthcare Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-mock>=3.12.0",
            "black>=23.11.0",
            "flake8>=6.1.0",
            "mypy>=1.7.0",
        ],
        "docs": [
            "sphinx>=7.1.0",
            "sphinx-rtd-theme>=1.3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "healthsync-patient-consent=agents.patient_consent.agent:main",
            "healthsync-data-custodian=agents.data_custodian.agent:main",
            "healthsync-research-query=agents.research_query.agent:main",
            "healthsync-privacy=agents.privacy.agent:main",
            "healthsync-metta=agents.metta_integration.agent:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)