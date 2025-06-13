from setuptools import setup, find_packages

setup(
    name="buffer",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "flask>=2.0.0",
        "flask-cors>=3.0.0",
        "requests>=2.25.0",
        "click>=8.0.0",
        "apscheduler>=3.9.0",
        "python-dateutil>=2.8.0",
        "croniter"
    ],
    entry_points={
        "console_scripts": [
            "buffer=buffer.cli:cli"
        ]
    },
    package_data={
        "buffer": [
            "frontend/build/**/*",
            "frontend/build/**/.*",
            "*.db",
            "frontend/public/**/*"
        ]
    },
    python_requires=">=3.8",
    author="Lucas",
    author_email="your.email@example.com",
    description="A message buffer platform with web interface",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/buffer",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
    ],
) 