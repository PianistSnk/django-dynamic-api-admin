from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="django-dynamic-api-admin",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A通用 Django Admin 组件，用于动态展示和管理 REST API 数据",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/django-api-admin",
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
    extras_require={
        "full": [
            "django-simpleui>=2022.0",
            "more-admin-filters>=1.8",
        ],
    },
    keywords="django admin api rest dynamic",
)
