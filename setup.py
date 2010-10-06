from setuptools import setup, find_packages
import os

version = '0.5dev'

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()


description_parts = (
    read("README.rst"),
    '',
    read("transmogrify", "zine", "README.rst"),
    '',
    read("docs", "HISTORY.rst"),
    '',
    )
long_description = "\n".join(description_parts)

setup(
    name='transmogrify.zine',
    version=version,
    description="A transmogrifier source for Zine Atom exports",
    long_description=long_description,
    classifiers=[
        "Programming Language :: Python",
        "Topic :: Text Processing :: Markup :: XML",
        ],
    keywords='zine transmogrifier atom xml source',
    author='Six Feet Up, Inc.',
    author_email='info@sixfeetup.com',
    url='http://www.sixfeetup.com',
    license='GPL',
    packages=find_packages(exclude=['ez_setup']),
    namespace_packages=['transmogrify'],
    include_package_data=True,
    install_requires=[
        'setuptools',
        'lxml',
        'python-dateutil',
        'collective.transmogrifier',
        ],
    zip_safe=False,
    )
