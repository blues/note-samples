#!bash

rm -rf archive

mkdir -p archive


cp ./app/*.py archive

#rm archive/__init__.py

# change version number for doing end-to-end testing
sed -i 's/"minor": 0/"minor": 1/' ./archive/version.py

cd archive
#generate TAR-file with all Python files in "archive" folder
tar cfv ../update.tar *.py
#generate TAR-file with just "version.py"
tar cfv ../update_version.tar version.py

cd ..


