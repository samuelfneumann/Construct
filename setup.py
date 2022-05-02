from setuptools import setup


setup(
    # Needed to silence warnings (and to be a worthwhile package)
    name='Construct',
    url='https://github.com/samuelfneumann/construct',
    author='Samuel Neumann',
    author_email='sfneuman@ualberta.ca',
    # Needed to actually package something
    packages=['construct'],
    # Needed for dependencies
    install_requires=[],
    # *strongly* suggested for sharing
    version='0.1',
    # The license can be anything you like
    license='MIT',
    description='Construct any object from a configuration file',
    # We will also need a readme eventually (there will be a warning)
    long_description=open('README.md').read(),
)
