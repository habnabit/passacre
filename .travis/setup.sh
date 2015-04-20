case "$_COMPILER" in
    clang)
        sudo apt-get install clang-3.4
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
