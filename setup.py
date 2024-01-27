import sys

from setuptools import Extension, setup

if sys.platform == "linux":
    extra_compile_args = [
        "-Wall",
        "-Wextra",
        "-Wpedantic",
        "-Werror",
        # disabling this because implicit zero initialized fields are fine IMO
        "-Wno-missing-field-initializers",
    ]

else:
    extra_compile_args = []

setup(
    name="squall",
    version="1.0.0",
    ext_modules=[
        Extension(
            "squall.util",
            ["squall/util.c"],
            libraries=["sqlite3"],
            py_limited_api=True,
            extra_compile_args=extra_compile_args,
        ),
    ],
    entry_points={"console_scripts": ["squall=squall.__main__:main"]},
    packages=["squall"],
    package_data={"squall": ["py.typed"]},
    include_package_data=True,
)
