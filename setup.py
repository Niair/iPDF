from setuptools import find_packages, setup
from typing import List
from pathlib import Path

HYPHEN_E_DOT = '-e .'

def get_requirements(file_path: str) -> List[str]:
    """Read requirements from file"""
    requirements = []
    with open(file_path, 'r') as file:
        requirements = file.readlines()
        requirements = [req.strip() for req in requirements]
        
        if HYPHEN_E_DOT in requirements:
            requirements.remove(HYPHEN_E_DOT)
    
    return requirements

# Read long description
long_description = ""
readme_path = Path(__file__).parent / "README.md"
if readme_path.exists():
    long_description = readme_path.read_text(encoding="utf-8")

setup(
    name='ipdf',
    version='2.0.0',
    author='Nihal',
    author_email='nihalk2180@outlook.com',
    description='Multimodal PDF chat application with RAG - 100% FREE',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=get_requirements('requirements.txt'),
    python_requires='>=3.11',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
    entry_points={
        'console_scripts': [
            'ipdf=ui.app:main',
        ],
    },
)
