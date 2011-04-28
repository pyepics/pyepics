installdir='/www/apache/htdocs/software/python/pyepics3'

srcdir=$installdir/src

# 
mv $srcdir/pyepics* $srcdir/older/.
cp -pr Changelog INSTALL README.txt $srcdir/.
cp -pr dist/*  $srcdir/.

echo 'use   python setup.py sdist upload  to upload to PyPI'
echo 'then run upload_wininst.bat from Windows to upload Win installers'

