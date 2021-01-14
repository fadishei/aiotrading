import setuptools

with open('README.md', 'r', encoding='utf-8') as fh:
    readme = fh.read()

with open("requirements.txt", encoding="utf-8") as r:
    requirements = [i.strip() for i in r]

setuptools.setup(
    name='aiotrading',
    version='0.0.1',
    author='Hamid Fadishei',
    author_email='fadishei@yahoo.com',
    description='Async trading library based on asyncio',
    long_description=readme,
    long_description_content_type='text/markdown',
    url='https://github.com/fadishei/aiotrading',
    license='GPLv3+',
    packages=setuptools.find_packages(),
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Financial and Insurance Industry',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries',
    ],
    keywords="trading asyncio binance restful websockets",
    python_requires='>=3.6',
    install_requires=requirements,
)