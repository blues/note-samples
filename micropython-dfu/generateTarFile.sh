#!bash

mkdir -p archive


cp ./src/*.py archive

rm archive/__init__.py

sed -i 's/"minor": 0/"minor": 1/' ./archive/version.py

cd archive
tar cfv ../update.tar *.py
cd ..


