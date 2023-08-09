from setuptools import setup

setup(
    name='vimeops',
    version='1.0.0',
    py_modules=['vimeops'],
    install_requires=[
        'Click',
    ],
    entry_points={
        'console_scripts': [
            'vimeops = app.vimeops:main',
        ],
    },
)
