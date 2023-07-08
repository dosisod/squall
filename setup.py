from setuptools import setup, Extension

setup(
    name="squall",
    version="1.0.0",
    ext_modules=[
        Extension(
            "squall.util",
            ["squall/util.c"],
            libraries=["sqlite3"],
            py_limited_api=True,
        ),
    ],
    entry_points={
        "console_scripts": ["squall=squall.__main__:main"]
    },
    packages=["squall"],
    package_data={"squall": ["py.typed"]},
    include_package_data=True,
)
