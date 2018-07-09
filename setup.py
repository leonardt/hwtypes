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

setup(
    name='bit_vector',
    url='https://github.com/leonardt/bit_vector',
    author='Leonard Truong',
    author_email='lenny@cs.stanford.edu',
    version='0.26-alpha',
    description='A BitVector class for Python',
    scripts=[],
    packages=[
        "bit_vector",
    ],
    install_requires=['numpy'],
    # python_requires='>=3.6'
)
