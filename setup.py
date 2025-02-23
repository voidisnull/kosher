from setuptools import setup, find_packages

setup(
    name='kosher-cli',
    version='0.0.3',
    description='Kosher - Language Environment Manager',
    author='Saksham',
    author_email='voidisnull@duck.com',
    url='https://github.com/voidisnull/kosher',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'docker>=7.0.0',
        'rich>=13.0.0'
    ],
    entry_points={
        'console_scripts': [
            'kosher=kosher_cli.main:main',
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.10',
    include_package_data=True,
)
