from setuptools import setup
# from pip.req import parse_requirements

# parse_requirements() returns generator of pip.req.InstallRequirement objects

# install_requires = []
# extra_requires = {}
# for item in parse_requirements("requirements.txt", session=False):
#     req = str(item.req)
#     if item.markers is not None:
#         req += ";" + str(item.markers)
#     install_requires.append(req)

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='hwtypes',
    url='https://github.com/leonardt/hwtypes',
    author='Leonard Truong',
    author_email='lenny@cs.stanford.edu',
    version='1.4.0',
    description='Python implementations of fixed size hardware types (Bit, '
                'BitVector, UInt, SInt, ...) based on the SMT-LIB2 semantics',
    scripts=[],
    packages=[
        "hwtypes",
    ],
    install_requires=['pysmt', 'z3-solver', 'gmpy2'],
    long_description=long_description,
    long_description_content_type="text/markdown"
    # python_requires='>=3.6'
)
