from gdpr.version import get_version

from setuptools import setup, find_packages

setup(
    name='django-GDPR',
    version=get_version(),
    description='Library for GDPR implementation',
    author='Druids',
    author_email='matllubos@gmail.com',
    url='https://github.com/matllubos/django-GDPR',
    license='MIT',
    package_dir={'gdpr': 'gdpr'},
    include_package_data=True,
    packages=find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    install_requires=[
        'django>=1.10',
        'django-chamber>=0.4.0',
    ],
    zip_safe=False
)
