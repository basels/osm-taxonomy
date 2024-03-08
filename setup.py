import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="osm-taxonomy",
    version="0.0.1",
    author="Basel Shbita",
    author_email="basel921@gmail.com",
    description="A tool for processing OpenStreetMap data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/basels/osm-taxonomy",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
    install_requires=[
        'pandas',
        'tqdm',
        'treelib',
        'lxml'
    ]
)