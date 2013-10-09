Pepa
====
Hierarchical substitution templating for SaltStack configuration also support's the use of Jinja2.

Build RPM
---------

*Pre-requisites*

    $ sudo yum install -y pandoc rpm-build

    $ git clone ...
    $ cd pepa
    $ ./build_venv.sh
    $ make

Example
-------

    $ cd pepa/src
    $ ./pepa.py -c ../example/conf/pepa.conf --host foobar.example.com -d

License
=======
See the file LICENSE.
