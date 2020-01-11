from setuptools import setup, find_packages


setup(
    name='mkdocs-tooltipster-links-plugin',
    version='0.1.0',
    description='An MkDocs plugin',
    long_description='An MkDocs plugin that adds tooltips to preview the content of page links using tooltipster',
    keywords='mkdocs',
    url='https://github.com/midnightprioriem/mkdocs-tooltipster-links-plugin',
    download_url='https://github.com/midnightprioriem/mkdocs-tooltipster-links-plugin/archive/v_010.tar.gz',
    author='Zach Hannum',
    author_email='zacharyhannum@gmail.com',
    license='MIT',
    python_requires='>=2.7',
    install_requires=[
        'mkdocs>=1.0.4',
        'beautifulsoup4>=4.8.2'
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7'
    ],
    packages=find_packages(),
    entry_points={
        'mkdocs.plugins': [
            'tooltipster-links = mkdocs_tooltipster_links_plugin.plugin:TooltipsterLinks'
        ]
    }
)
