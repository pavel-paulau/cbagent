from setuptools import setup

version = '1.17.1'

setup(
    name='cbagent',
    version=version,
    author='Couchbase',
    license='Apache Software License',
    packages=[
        'cbagent',
        'cbagent.cli_wrappers',
        'cbagent.collectors',
        'cbagent.collectors.libstats'
    ],
    entry_points={
        'console_scripts': [
            'at_collector = cbagent.cli_wrappers.at_collector:main',
            'atop_collector = cbagent.cli_wrappers.atop_collector:main',
            'latency_collector = cbagent.cli_wrappers.latency_collector:main',
            'ns_collector = cbagent.cli_wrappers.ns_collector:main',
            'ps_collector = cbagent.cli_wrappers.ps_collector:main',
            'sgw_collector = cbagent.cli_wrappers.sgw_collector:main',
            'xdcr_lag_collector = cbagent.cli_wrappers.xdcr_lag_collector:main',
        ]
    },
    include_package_data=True,
    install_requires=[
        'couchbase==1.2.0',
        'decorator',
        'eventlet==0.12.1',
        'fabric==1.8.0',
        'logger',
        'requests==2.1.0',
        'seriesly',
        'spring'
    ],
)
