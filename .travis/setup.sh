curl https://sh.rustup.rs/ | sh -s -- -y --default-toolchain nightly
export PATH="$HOME/.cargo/bin:$PATH"

curl https://nixos.org/nix/install | bash
source ~/.nix-profile/etc/profile.d/nix.sh
nix-env -iA nixpkgs.capnproto

case "$_COMPILER" in
    clang)
        sudo apt-get update
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
    nix-env -iA nixpkgs.kcov
fi
