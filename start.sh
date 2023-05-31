#!/bin/bash

PUID=${PUID:-100}
PGID=${PGID:-99}

groupmod -o -g "$PGID" titlecardmaker
usermod -o -u "$PUID" titlecardmaker

chown -R titlecardmaker:titlecardmaker /maker /config

exec gosu titlecardmaker "$@"