from setuptools import setup
from Cython.Build import cythonize

setup(
    ext_modulues=cythonize("main.py")
)
