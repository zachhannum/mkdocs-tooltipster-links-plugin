from setuptools import setup, find_packages

version="0.2.2"

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()
with open("requirements.txt") as f:
    required = f.read().splitlines()
setup(
    name="mkdocs-preview-links-plugin",
    version=version,
    description="An MkDocs plugin",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="mkdocs, preview, tooltipster, tooltipst",
    url="https://github.com/Mara-Li/mkdocs-tooltipster-links-plugin",
    author="Mara-Li",
    author_email="mara-li@outlook.fr",
    license="MIT",
    python_requires=">=2.7",
    install_requires=required,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    packages=find_packages(),
    entry_points={
        "mkdocs.plugins": [
            "tooltipster-links ="
            " mkdocs_tooltipster_links_plugin.plugin:TooltipsterLinks"
        ]
    },
)
