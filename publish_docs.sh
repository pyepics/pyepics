installdir='/www/apache/htdocs/software/python/pyepics3'
docbuild='doc/_build'

cd doc 
echo '# Making docs'

# make all
cd ../
echo '# Building tarball of docs'
mkdir _tmpdoc
cp -pr doc/pyepics.pdf     _tmpdoc/pyepics.pdf
cp -pr doc/_build/html/*    _tmpdoc/.
cd _tmpdoc
tar czf ../../pyepics_docs.tar.gz .
cd ..
rm -rf _tmpdoc 

# 

echo "# Switching to gh-pages branch"
git checkout gh-pages

if  [ $? -ne 0 ]  ; then 
  echo ' failed.'
  exit 
fi

tar xzf ../pyepics_docs.tar.gz .

echo "# commit changes to gh-pages branch"
git commit -am "changed docs"

if  [ $? -ne 0 ]  ; then 
  echo ' failed.'
  exit 
fi

echo "# Pushing docs to github"
git push


echo "# switch back to master branch"
git checkout master

if  [ $? -ne 0 ]  ; then 
  echo ' failed.'
  exit 
fi
