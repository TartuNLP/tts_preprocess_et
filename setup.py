from setuptools import setup, find_packages

setup(
    name='tts_preprocess_et',
    version='1.0.1',
    packages=find_packages(),
    license='MIT',
    description='Preprocessing for Estonian text-to-speech applications',
    long_description=open('readme.md').read(),
    install_requires=['estnltk>=1.7.0'],
    python_requires='>=3.10',
    include_package_data=True,
    url='https://github.com/TartuNLP/tts_preprocess_et',
    author='TartuNLP',
    author_email='ping@tartunlp.ai'
)