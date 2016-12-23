#!/bin/bash -lex
mkdir -p ~/build /build/wheelhouse
cd ~/build
cmake /build/passacre-backend -DCMAKE_BUILD_TYPE=Release
make
cp -v passacre_backend-*.whl /build/wheelhouse
