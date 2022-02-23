#!/usr/bin/env bash

echo "Downloading new version of Cello"

rm cello

wget http://esox3.scilifelab.se:8084/dist/linux/cello

chmod +x cello

./cello &