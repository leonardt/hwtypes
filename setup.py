from setuptools import setup
from pip.req import parse_requirements

# parse_requirements() returns generator of pip.req.InstallRequirement objects

install_requires = []
extra_requires = {}
for item in parse_requirements("requirements.txt", session=False):
    req = str(item.req)
    if item.markers is not None:
        req += ";" + str(item.markers)
    install_requires.append(req)

setup(
    name='bit_vector',
    version='0.20-alpha',
    description='A BitVector class for Python',
    scripts=[],
    packages=[
        "bit_vector",
    ],
    install_requires=install_requires,
    # python_requires='>=3.6'
)
