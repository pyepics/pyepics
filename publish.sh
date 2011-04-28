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

echo '# Publishing PyEpics Docs'
#cp -pr $docbuild/latex/epics.pdf $installdir/pyepics3.pdf
#cp -pr $docbuild/html/*          $installdir/.

echo '# Publishing PyEpics Docs'
mkdir _tmpdoc
cp -pr $docbuild/latex/epics.pdf _tmpdoc/pyepics.pdf
cp -pr $docbuild/html/*          _tmpdoc/.
cd _tmpdoc
tar cvzf ../../pyepics_docs.tar.gz .
cd ..
rm -rf _tmpdoc _images _sources _static *.html *.js *.inv pyepics3.pdf

git checkout gh-pages
tar xvzf ../pyepics_docs.tar.gz .
git commit -am "changed docs"
git push
git checkout master

