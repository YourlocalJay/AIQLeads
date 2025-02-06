from setuptools import setup, find_packages

setup(
    name="aiqleads",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "aiqleads-track=aiqleads.scripts.track:main",
        ],
    },
)