# setup.py
from setuptools import find_packages, setup
from typing import List
from pathlib import Path

REQ_FILE = "requirements.txt"

def get_requirements(file_path: str = REQ_FILE) -> List[str]:
    path = Path(file_path)
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        reqs = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    reqs = [r for r in reqs if r != "-e ."]
    return reqs

setup(
    name="iPDF",
    version="1.2.0",
    author="Nihal",
    author_email="nihalk2180@outlook.com",
    description="iPDF - Chat with PDFs (modular Streamlit + LLM assistant)",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=get_requirements(),
    include_package_data=True,
    python_requires=">=3.11",
)