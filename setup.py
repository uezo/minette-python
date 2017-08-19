from setuptools import setup, find_packages
from minette import __version__

setup(
    name="minette",
    version=__version__,
    url="https://github.com/uezo/minette-python",
    author="uezo",
    author_email="uezo@uezo.net",
    maintainer="uezo",
    maintainer_email="uezo@uezo.net",
    description="Minette is a micro Bot framework. Session and user management, Natural language analyzing and architecture for multi-skill/character bot are ready-to-use",
    packages=find_packages(exclude=["imoutobot*", "examples*", "tests*"]),
    install_requires=["requests", "pytz"],
    license="Apache v2",
    entry_points={
        "console_scripts": [
            "minette=minette.script.console:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3"
    ]
)
