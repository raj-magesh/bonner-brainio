BrainIO Technical Specification
===============================

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in RFC 2119.

BrainIO defines three types of entity:

* BrainIO Data Assembly (hereafter, "Data Assembly")
* BrainIO Stimulus Set (hereafter, "Stimulus Set")
* BrainIO Catalog (hereafter, "Catalog")

.. _specification.assembly:

BrainIO Data Assembly
---------------------

A Data Assembly

* MUST be a `netCDF-4 <https://docs.unidata.ucar.edu/netcdf-c/current/file_format_specifications.html#netcdf_4_spec>`_ file whose

    * root `group <https://docs.unidata.ucar.edu/netcdf-c/current/file_format_specifications.html#groups_spec>`_

        * MUST contain exactly one `variable <https://docs.unidata.ucar.edu/netcdf-c/current/file_format_specifications.html#vars_spec>_` corresponding to experimental data
        * MAY contain other `variables <https://docs.unidata.ucar.edu/netcdf-c/current/file_format_specifications.html#vars_spec>_` corresponding to metadata with the same `dimensions <https://docs.unidata.ucar.edu/netcdf-c/current/file_format_specifications.html#dims_spec>`_ as the experimental data

    * non-root `groups <https://docs.unidata.ucar.edu/netcdf-c/current/file_format_specifications.html#groups_spec>`_

        * MAY contain `variables <https://docs.unidata.ucar.edu/netcdf-c/current/file_format_specifications.html#vars_spec>_` corresponding to metadata with `dimensions <https://docs.unidata.ucar.edu/netcdf-c/current/file_format_specifications.html#dims_spec>`_ different from the experimental data

* MUST contain the string-type `global attributes <https://docs.unidata.ucar.edu/netcdf-c/current/file_format_specifications.html#atts_spec>`_ ``identifier`` and ``stimulus_set_identifier``

.. _specification.stimulus_set:

BrainIO Stimulus Set
--------------------

A BrainIO Stimulus Set comprises

    * a `ZIP <https://datatracker.ietf.org/doc/html/rfc4180>`_ archive (hereafter, "Stimulus Set ZIP Archive") that MUST contain files where each corresponds to an experimental stimulus
    * a `CSV <https://datatracker.ietf.org/doc/html/rfc4180>`_ file (hereafter, "Stimulus Set CSV File")

        * where each row MUST contain metadata about one file in the Stimulus Set ZIP Archive
        * that MUST have a `header row <https://datatracker.ietf.org/doc/html/rfc4180>`_ of column names comprising lowercase letters, numerals, and underscores
        * that MUST contain the columns

            * ``stimulus_id``, that MUST have alphanumeric entries that are unique within the column
            * ``filename``, that MUST have entries representing the filepaths of the corresponding files within the Stimulus Set ZIP Archive

        * that MAY contain additional metadata columns

.. _specification.catalog:

BrainIO Catalog
---------------

A BrainIO Catalog

* MUST be a `CSV file <https://datatracker.ietf.org/doc/html/rfc4180>`_

    * where each row

        * MUST contain metadata corresponding to exactly one of

            * a Data Assembly
            * a Stimulus Set ZIP Archive
            * a Stimulus Set CSV File

    * where

        * if a row contains metadata corresponding to a Stimulus Set ZIP Archive, another row corresponding to the Stimulus Set CSV File MUST be present
        * if a row contains metadata corresponding to a Data Assembly

    * that MUST have a `header row <https://datatracker.ietf.org/doc/html/rfc2119>`_  of column names comprising lowercase letters, numerals, and underscores
    * that MUST contain the columns

        * ``identifier``
        * ``lookup_type``
        * ``location_type``
        * ``location``
        * ``sha1``, that MUST be the `SHA1 hash <https://datatracker.ietf.org/doc/html/rfc3174>`_ of the file
        * ``stimulus_set_identifier``
        * ``class``

* MUST have a string **identifier** that SHOULD be globally unique
* MUST contain a

Each row of the BrainIO Catalog refers to either a BrainIO Data Assembly or a BrainIO Stimulus Set.

In each row of the BrainIO Catalog, the columns MUST contain the following information:

* ``identifier``: the ``identifier`` of the BrainIO Data Assembly or

Metadata referring to a BrainIO Data Assembly is stored in a BrainIO Catalog as a single row

    * ``identifier``

        * to ``identifiers`` of BrainIO Data Assemblies and BrainIO Stimulus Sets
    * ``lookup_type``, which MUST be ``stimulus_set``



Catalog
-------


.. _spec_stimulus_set:

Stimulus Set
------------
