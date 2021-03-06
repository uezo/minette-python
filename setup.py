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
    description="Minette is a minimal and extensible chatbot framework. It is extremely easy to create chatbot and also enables you to make your chatbot more sophisticated and multi-skills, with preventing to be spaghetti code.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=["examples*", "develop*", "tests*"]),
    install_requires=["pytz", "schedule"],
    license="Apache v2",
    classifiers=[
        "Programming Language :: Python :: 3"
    ]
)
