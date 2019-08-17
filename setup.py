"""sx - setup.py"""
import sx
import setuptools

VERSION = sx.__version__
LONG_DESC = open('README.md').read()
DOWNLOAD = "https://github.com/itsmealves/sx/archive/sx-%s.tar.gz" % VERSION

setuptools.setup(
    name="sx",
    version=VERSION,
    author="Gabriel Alves",
    long_description=LONG_DESC,
    author_email="gabriel.alves@pickcells.bio",
    long_description_content_type="text/markdown",
    description="Framework to manage gRPC-based microservices application",
    keywords="sx microservices rpc grpc Framework",
    license="MIT",
    url="https://github.com/itsmealves/sx",
    download_url=DOWNLOAD,
    classifiers=[],
    packages=["sx"],
    entry_points={"console_scripts": ["sx=sx.__main__:main"]},
    python_requires=">=3.5",
    test_suite="tests",
    include_package_data=True,
    zip_safe=False)