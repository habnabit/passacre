from distutils.core import setup

setup(
    name='passacre',
    packages=['passacre', 'passacre.test'],
    entry_points={
        'console_scripts': ['passacre = passacre.application:main'],
    },
)
