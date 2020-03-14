from setuptools import setup
from setuptools import find_packages

setup(
    name='pen',
    version='0.5.0',
    packages=find_packages(),
    author='Emmett McQuinn',
    license='LICENSE.txt',
    description='Hobby project for a robotic pen plotter',
    test_suite='tests',
    python_requires='>=2.7.0',
    entry_points={
        'console_scripts': ['robopen=robopen:main'],
    },
    install_requires=[
        'numpy >= 1.17.0',
        'halo >= 0.0.29',
        'tqdm >= 4.0.0',
        'pyserial >= 3.4',
    ],
)
