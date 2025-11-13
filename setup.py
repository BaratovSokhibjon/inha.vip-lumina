from setuptools import setup, find_packages

setup(
    name='lumina',
    version='2.0.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    entry_points={
        'console_scripts': [
            'lumina=lumina.cli:main',
        ],
    },
    install_requires=[
        'Flask>=2.0.0',
        'PyYAML>=6.0',
        'requests>=2.28.0',
    ],
)