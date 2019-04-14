from setuptools import setup, find_packages

with open("./minette/version.py") as f:
    exec(f.read())

setup(
    name="minette",
    version=__version__,
    url="https://github.com/uezo/minette-python",
    author="uezo",
    author_email="uezo@uezo.net",
    maintainer="uezo",
    maintainer_email="uezo@uezo.net",
    description="Minette is a micro chatbot framework. Session and user management, natural language analyzing and architecture for multi-skill/character bot are ready-to-use",
    packages=find_packages(exclude=["examples*", "imoutobot*", "tests*"]),
    install_requires=["requests", "pytz", "schedule"],
    license="Apache v2",
    classifiers=[
        "Programming Language :: Python :: 3"
    ]
)
