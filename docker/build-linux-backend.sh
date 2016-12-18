#!/bin/bash -le
mkdir -p ~/build /build/wheelhouse
cd ~/build
cmake /build/libpassacre -DCMAKE_BUILD_TYPE=Release
PATH="/opt/python/cp27-cp27mu/bin:$PATH" make
cp -v passacre_backend-*.whl /build/wheelhouse
