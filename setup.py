from setuptools import find_packages, setup

from gdpr.version import get_version

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
        'Framework :: Django :: 1.10',
        'Framework :: Django :: 1.11',
        'Framework :: Django :: 2.0',
        'Framework :: Django :: 2.1',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3 :: Only',
        'Intended Audience :: Developers',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    install_requires=[
        'django>=1.10',
        'django-chamber>=0.4.0',
        'tqdm>=4.28.1',
        'pyaes>=1.6.1',
    ],
    zip_safe=False
)
