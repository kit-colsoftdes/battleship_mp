.. battleship_mp documentation master file, created by
   sphinx-quickstart on Tue Jul 11 09:26:28 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

KIT CSD Battleship MP documentation
===================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:
   :hidden:

   client
   player
   server

.. image:: https://readthedocs.org/projects/battleship-mp/badge/?version=latest
    :target: https://battleship-mp.readthedocs.io/en/latest
    :alt: Documentation Status

.. image:: https://img.shields.io/pypi/v/kcsd-battleship-mp.svg
    :alt: Available on PyPI
    :target: https://pypi.python.org/pypi/kcsd-battleship-mp/

.. image:: https://img.shields.io/github/license/kit-colsoftdes/battleship_mp.svg
    :alt: License
    :target: https://github.com/kit-colsoftdes/battleship_mp/blob/main/LICENSE

The :py:mod:`battleship_mp` provides a client/server
for use as part of the KIT course Collaborative Software Design.

You can install the package directly via ``pip``;
only Python >= 3.8 is required.

.. code:: bash

    ~ $ python3 -m pip install kcsd-battleship-mp

.. warning::

   The client and server do not authenticate peers in any way.
   Avoid sending private information, e.g. as part of the player identifier.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
