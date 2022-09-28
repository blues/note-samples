#!bash

# set target folder
targetFolder=_archive

echo 'Using target folder: ' $targetFolder

rm -rf $targetFolder

mkdir -p $targetFolder


cp ./app/*.py $targetFolder
cp ./src/*.py $targetFolder
cp -r ./lib $targetFolder/lib

# change version number for doing end-to-end testing
sed -i 's/"minor": 0/"minor": 1/' ./$targetFolder/version.py

cd $targetFolder
#generate TAR-file with all Python files in target folder
find . -name "*.py" | tar cfv ./update.tar -T -
#generate TAR-file with just "version.py"
tar cfv ./update_version.tar version.py

cd ..


