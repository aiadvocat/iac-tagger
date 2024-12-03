from setuptools import setup, find_packages

setup(
    name="iac-tagger",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pyyaml>=6.0.1",
        "python-hcl2>=4.3.2",
        "gitpython>=3.1.31",
    ],
    entry_points={
        "console_scripts": [
            "iac-tagger=iac_tagger.main:main",
        ],
    },
) 