Maintenance
===========

.. note::

    This page is only relevant for maintainers of :py:mod:`battleship_mp`.

Releases
--------

The package follows `Semantic Versioning`_
and is automatically published to PyPI using GitHub actions.
To trigger a release:

1. Commit a new version
    - Adjust and commit the ``version`` in ``pyproject.toml``
    - Create a git tag for on commit (e.g. via ``git tag -a "v1.1.2" -m "description"``)
    - Push the commit and tags to GitHub

2. Publish the new release
    - Create a new `GitHub release`_ from the recent version tag
    - Wait for the action to push the release to PyPI

.. _Semantic Versioning: https://semver.org
.. _GitHub release: https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases
