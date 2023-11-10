from pybind11.setup_helpers import Pybind11Extension, build_ext
from setuptools import setup

__version__ = "0.0.1"

source_files = """
src/koelsynth.cpp
""".split()

ext_modules = [
    Pybind11Extension(
        "koelsynth",
        source_files,
    )
]

setup(
    name="koelsynth",
    version=__version__,
    author="Vinay Krishnan",
    author_email="nk.vinay@zohomail.in",
    url="https://github.com/charstorm/koelsynth",
    description="A simple music synthesis library in C++ wrapped using pybind11",
    long_description="",
    ext_modules=ext_modules,
    extras_require={},
    install_requires=["pybind11"],
    cmdclass={"build_ext": build_ext},
    zip_safe=False,
    python_requires=">=3.10",
)
