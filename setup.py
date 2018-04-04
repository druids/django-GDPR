from setuptools import setup, find_packages

setup(
    name='django-anonymization',
    version='0.1',
    description='Library for anonymizing model fields',
    author='lymet',
    author_email='lymet@example.org',
    url='https://django-anonymization.example.org',
    license='LGPL',
    package_dir={'anonymization': 'anonymization'},
    include_package_data=True,
    packages=find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    install_requires=[
        'django>=1.9',
        'django-chamber>=0.3.7',
    ],
    dependency_links=[
        'https://github.com/druids/django-chamber/tarball/0.3.7#egg=django-chamber-0.3.7'
    ],
    zip_safe=False
)
