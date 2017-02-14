from distutils.core import setup

exec(open("lib/_version.py").read())

setup(name="ds2017",
    description="ds practice work",
    version=__version__,
    author="",
    author_email="",
    package_dir={"ds2017chat":"ds2017chat"},
    packages=["lib"],
    scripts=["bin/scripts"]
)
