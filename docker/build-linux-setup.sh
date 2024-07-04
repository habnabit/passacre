#!/bin/sh -eux

python /root/get-pip.py

cat >/etc/yum.repos.d/devtools-2.repo <<'EOF'
[testing-devtools-2-centos-$releasever]
name=testing 2 devtools for CentOS $releasever
baseurl=http://people.centos.org/tru/devtools-2/$releasever/$basearch/RPMS
gpgcheck=0
EOF

yum install -y \
    make cmake ca-certificates tar git \
    kernel-devel-`uname -r` \
    devtoolset-2-binutils devtoolset-2-gcc devtoolset-2-gcc-c++

/root/rustup-init -y --default-toolchain nightly
echo '. ~/.cargo/env' >> ~/.bash_profile

cd /root
tar xf capnproto-c++-0.5.3.tar.gz
cd capnproto-c++-0.5.3
./configure
make install
