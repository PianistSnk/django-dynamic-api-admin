from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="django-dynamic-api-admin",
    version="2.0.0",
    author="PianistSnk",
    author_email="juventus_u23@icloud.com",
    description="A Django Admin component for managing REST API data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/PianistSnk/django-dynamic-api-admin",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Framework :: Django",
        "Framework :: Django :: 3.2",
        "Framework :: Django :: 4.0",
        "Framework :: Django :: 5.0",
    ],
    python_requires=">=3.8",
    install_requires=[
        "Django>=3.2",
        "redis>=4.0.0",
        "requests>=2.28.0",
    ],
    keywords="django admin api rest dynamic",
)
