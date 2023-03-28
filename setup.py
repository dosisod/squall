from distutils.core import setup, Extension

def main():
    setup(
        name="squall",
        version="1.0.0",
        ext_modules=[
            Extension("squall", ["squall/squall.c"], libraries=["sqlite3"]),
        ],
    )

if __name__ == "__main__":
    main()
