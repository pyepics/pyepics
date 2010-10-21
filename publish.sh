#!/bin/sh
#
#  "publish" a new version of the source distribution and documentation
#
#  Steps prior to publishing:
#   1.  run 'make_wininsts.bat' from a a Windows shell to build dist/*.exe
#   2.  run 'python setup.py sdist' from Linux 
#   3.  verify that the docs build without error.

installdir='/www/apache/htdocs/software/python/pyepics3'

srcdir=$installdir/src

docbuild='doc/_build'

cd doc
make all
cd ../

echo '# Publishing PyEpics'
cp -pr $docbuild/latex/epics.pdf $installdir/pyepics3.pdf
cp -pr $docbuild/html/*          $installdir/.
# 
mv $srcdir/epics* $srcdir/older/.
cp -pr Changelog INSTALL README.txt $srcdir/.
cp -pr dist/*  $srcdir/.
# 
