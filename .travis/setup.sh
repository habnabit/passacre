case "$_COMPILER" in
    clang)
        sudo apt-get install -y clang-3.4
        export CC='clang' LDSHARED='clang -shared'
        ;;
    gcc)
        export CC='gcc'
        ;;
    *)
        echo "unknown compiler $_COMPILER"
        exit 1
        ;;
esac

if [ -n "$_KCOV" ]; then
    sudo apt-get install -y libcurl4-openssl-dev libelf-dev libdw-dev binutils-dev libiberty-dev
    wget -O kcov.tar.gz https://github.com/SimonKagstrom/kcov/archive/v29.tar.gz
    tar xf kcov.tar.gz
    (cd kcov-29 && cmake . -DCMAKE_INSTALL_PREFIX:PATH="$HOME/.local" && make && make install)
    export PATH="$HOME/.local/bin:$PATH"
fi
