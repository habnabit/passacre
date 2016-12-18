#!/bin/bash -e
chown builder: /var/lib/builder/.cargo/registry
exec su -c "exec /build/docker/build-linux-backend.sh" builder
