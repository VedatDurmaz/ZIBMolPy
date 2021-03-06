ZIBMolPy
========

![ZIBMolPy](https://github.com/CMD-at-ZIB/ZIBMolPy/raw/master/docu/zgf_logo_trans_small.png)


What's this?
------------

<p align="justify">The core of the ZIBMolPy package is an implementation of the efficient, adaptive sampling algorithm ZIBgridfree, designed for characterizing the conformational space of molecules.</p>

<p align="justify">The original ZIBgridfree algorithm was designed by Marcus Weber and Holger Meyer in 2005, and, over the years, has been enhanced by Alexander Riemer, Susanna Röblitz and Lionel Walter. The theoretical framework of ZIBgridfree is provided by Conformation Dynamics, an idea coined by Peter Deuflhard and Christoph Schütte.</p>

<p align="justify">This implementation represents an evolution of the original ZIBgridfree as it couples the original algorithm to the state-of-the-art molecular dynamics engine <a href="http://www.gromacs.org">Gromacs</a>. This creates the possibility to apply ZIBgridfree to very large molecular systems.</p>

<p align="justify">ZIBMolPy is currently being developed by Alexander Bujotzek, Ole Schütt and Adam Nielsen in the working group of Marcus Weber at Zuse-Institute Berlin. A manuscript for publication is in preparation:</p>

* <p align="justify">A. Bujotzek, O. Schütt, K. Fackeldey, M. Weber: ZIBgridfree: Efficient conformational analysis by meshless uncoupling-coupling</p>

License
-------

This software package is released under the LGPL 3.0, see LICENSE file.

Screenshots
-----------

![ZIBgridfree Browser](https://github.com/CMD-at-ZIB/ZIBMolPy/raw/develop/docu/mini_screen01.png)

ZIBgridfree Browser, the graphical user interface of ZIBgridfree.

![ZIBgridfree Browser](https://github.com/CMD-at-ZIB/ZIBMolPy/raw/develop/docu/mini_screen02.png)

Monitor the distribution of your internal coordinates as it is sampled.

![ZIBgridfree Browser](https://github.com/CMD-at-ZIB/ZIBMolPy/raw/develop/docu/mini_screen03.png)

Analyze thermodynamics and identify metastable conformations.

Installation
------------

#### Prerequisites

You have to install a bunch of packages. On Ubuntu/Debian you can simply type:

`sudo apt-get install python-numpy python-scipy python-matplotlib python-gtk2 gromacs`

#### Download

1. Download the current 'master' version as [zipball](https://github.com/CMD-at-ZIB/ZIBMolPy/zipball/master) or [tarball](https://github.com/CMD-at-ZIB/ZIBMolPy/tarball/master).

2. Extract it with e.g. <br />
`tar -xvzf CMD-at-ZIB-ZIBMolPy-80c927a.tar.gz`

3. Go into the the directory: <br />
`cd CMD-at-ZIB-ZIBMolPy-xxxxxx`

Alternatively, use git to obtain the code: <br />
`git clone git://github.com/CMD-at-ZIB/ZIBMolPy.git` (read-only) <br />
`git clone git@github.com:CMD-at-ZIB/ZIBMolPy.git` (read+write)

#### System-wide installation

Run: <br />
`sudo make install`

#### Installation into home directory

1. Run <br />
`make install-home`

2. Add the following lines to your `.bashrc`: <br />
`export PYTHONPATH=$PYTHONPATH:~/lib/pythonX.X/site-packages/` <br />
`export PATH=$PATH:~/bin/`

#### Installation into custom location

1. Run <br />
`make prefix=~/my_favorite_location install`

2. Add the following lines to your `.bashrc`: <br />
`export PYTHONPATH=$PYTHONPATH:~/my_favorite_location/lib/pythonX.X/site-packages/` <br />
`export PATH=$PATH:~/my_favorite_location/bin/`

Testing
-------

You can run some tests to make sure everything is working as intended.

1. Go into the tests/ directory, which is located either in <br />
`/usr/share/zibmolpy/tests`
or <br />
`~/usr/share/zibmolpy/tests`, or according to your own prefix.

2. Choose one of the tests cases. The pentane_quick test takes the least amount of time to run.

3. Depending on your Gromacs version run either <br />
`zgf_test test-desc-seq-gromacs-4.0.7.xml` <br />
or <br />
`zgf_test test-desc-seq-gromacs-4.5.5.xml`

4. You can take a look at the results by using zgf_browser.

If tests fail due to differences in numerical values, you may be using a different version of Gromacs.

Documentation
-------------

For documentation, please refer to the wiki at:

[github.com/CMD-at-ZIB/ZIBMolPy/wiki](https://github.com/CMD-at-ZIB/ZIBMolPy/wiki)

The API documentation can be found here:

[cmd-at-zib.github.com/ZIBMolPy/apidocs/](http://cmd-at-zib.github.com/ZIBMolPy/apidocs/)
