from distutils.core import setup

description = open('README.txt').read()

setup(
    name = "iso-8601",
    version = "0.1.5",
    description = description,
    url = "http://hg.schinckel.net/iso-8601/",
    author = "Matthew Schinckel",
    author_email = "matt@schinckel.net",
    packages = [
        "iso8601",
    ],
    classifiers = [
        'Programming Language :: Python',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'Development Status :: 4 - Beta',
        'Topic :: Software Development :: Libraries',
    ],
)
