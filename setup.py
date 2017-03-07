from distutils.core import setup

exec(open("dschat/_version.py").read())

setup(name="ds2017",
    description="ds practice work",
    version=__version__,
    author="",
    author_email="",
    package_dir={"dschat":"dschat"},
    packages=["dschat", "dschat/daemon", "dschat/util", "dschat/util", "dschat/flask", "dschat/flask/app"],
    scripts=["bin/dschat"]
)
