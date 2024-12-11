from setuptools import setup, find_packages

with open('README.md') as f:
    long_description = f.read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='document-converter',
    version='0.1.0',
    description='Convert documents between different formats while preserving formatting',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Animality AI',
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'convert-doc=converter.converter:main',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
    python_requires='>=3.8',
)