"""sx - setup.py"""
import sx
import setuptools


VERSION = sx.__version__
LONG_DESC = open('README.md').read()
DOWNLOAD = "https://github.com/itsmealves/sx/releases/download/{0}/sx-{0}.tar.gz".format(VERSION)

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
    packages=[
        'sx',
        'sx.stubs',
        'sx.actions',
        'sx.actions.boot',
        'sx.actions.create'
    ],
    install_requires=[
        'grpcio>=1.22.0',
        'grpcio-tools>=1.22.0',
        'toml>=0.10.0',
        'libtmux>=0.8.2',
        'coolname>=1.1.0'
    ],
    entry_points={"console_scripts": ["sx=sx.__main__:main"]},
    python_requires=">=3.5",
    test_suite="tests",
    include_package_data=True,
    zip_safe=False)