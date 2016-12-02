===========
nelson
===========

As described in `python-packaging <https://python-packaging.readthedocs.io/en/latest/minimal.html/>`_ the best way to develop locally is with
::
    pip install -e .

To upload a new version, change the version number in setup.py and then run 
::
    python setup.py register sdist upload

It's best to test on testpypi first with the `-r pypitest` option.
