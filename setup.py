from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(name='pulsemixer',
    version='1.5.0',
    description='pulsemixer - CLI and curses mixer for PulseAudio',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/GeorgeFilipkin/pulsemixer',
    author='George Filipkin',
    author_email='botebotebot@gmail.com',
    license='MIT',
    scripts=['pulsemixer'],
    classifiers=[
        'Environment :: Console',
        'Environment :: Console :: Curses',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Topic :: Multimedia :: Sound/Audio :: Mixers',
        'Topic :: Utilities',
    ],
)
