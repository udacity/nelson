from setuptools import setup

setup(
    name='nelson',
    version='0.2.1',
    author='S. Charles Brubaker',
    author_email='cb@udacity.com',
    packages=['nelson'],
    entry_points={
        'console_scripts': [
            'nelson = nelson.developer:main_func'
        ],
    },
    url='http://github.com/udacity/nelson',
    license='MIT',
    description='Handling submission of code to Udacity for automatic feedback',
    keywords = 'Udacity Georgia Tech OMS',
    long_description=open('README.rst').read(),
    install_requires=[
        "requests >= 2.2.1",
        "requests-toolbelt >= 0.7.0",
    ],
)
