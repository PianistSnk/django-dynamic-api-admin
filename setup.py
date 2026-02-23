from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="django-dynamic-api-admin",
    version="2.1.0",
    author="PianistSnk",
    author_email="juventus_u23@icloud.com",
    description="无需编写 Django Model，直接用外部 API 数据管理",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/PianistSnk/django-dynamic-api-admin",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Framework :: Django",
    ],
    python_requires=">=3.8",
    install_requires=[
        "Django>=3.2",
        "requests>=2.28.0",
    ],
)
