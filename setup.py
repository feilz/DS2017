from distutils.core import setup

exec(open("dschat/_version.py").read())

setup(name="ds2017",
    description="ds practice work",
    version=__version__,
    author="",
    author_email="",
    package_dir={"dschat":"dschat"},
    packages=[
        "dschat",
        "dschat/daemon",
        "dschat/db",
        "dschat/util",
        "dschat/flask",
        "dschat/flask/app",
        "dschat/flask/app/forms"
    ],
    scripts=["bin/dschat"]
)
