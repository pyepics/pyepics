
Web Pages for Py-Epics 3:  Epics Channel Access for Python
=================================================================

This is the github documentation pages for PyEpics3

License
========

This code is distributed under the  Epics Open License

Usage
========

From the master branch, run publish.sh to build latest documentation and
make a tarball in '..'.

Then from gh-pages, unpack the tarball to this folder, and commit and push
all changes.

  git checkout master
  sh publish.sh
  git checkout gh-pages
  tar xvzf ../pyepics_docs.tgz
  git commit -am "updated docs again"
  git push
  git checkout master


