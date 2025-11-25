"""
================================================================================
setup.py - Python Package Setup
================================================================================
Version: 1.0.0
Date: 2025-11-25
Author: Stealth Deck Project

Package installation configuration.
================================================================================
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / 'README.md'
long_description = ''
if readme_file.exists():
    long_description = readme_file.read_text(encoding='utf-8')

# Read requirements
requirements_file = Path(__file__).parent / 'requirements.txt'
requirements = []
if requirements_file.exists():
    with open(requirements_file) as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name='stealth-deck',
    version='0.5.0',
    
    description='Stealth Deck - Covert AI Assistant',
    long_description=long_description,
    long_description_content_type='text/markdown',
    
    author='Stealth Deck Project',
    author_email='dev@stealthdeck.com',
    url='https://github.com/yourusername/stealth-deck',
    
    license='MIT',
    
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    
    python_requires='>=3.9',
    
    install_requires=requirements,
    
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
            'pytest-mock>=3.10.0',
            'black>=23.0.0',
            'flake8>=6.0.0',
            'mypy>=1.0.0',
            'pylint>=2.17.0',
        ],
        'docs': [
            'sphinx>=5.0.0',
            'sphinx-rtd-theme>=1.2.0',
        ],
    },
    
    entry_points={
        'console_scripts': [
            'stealth-deck=main:main',
        ],
    },
    
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: System :: Hardware',
        'Topic :: Security',
    ],
    
    keywords='raspberry-pi esp32 ai gemini security',
    
    project_urls={
        'Bug Reports': 'https://github.com/yourusername/stealth-deck/issues',
        'Source': 'https://github.com/yourusername/stealth-deck',
        'Documentation': 'https://stealth-deck.readthedocs.io',
    },
    
    include_package_data=True,
    
    package_data={
        'stealth_deck': [
            'data/fonts/*.ttf',
            'data/dictionaries/*.txt',
            'data/syntax/*.json',
            'config/*.json',
        ],
    },
    
    zip_safe=False,
)
