#!/bin/sh

PUID=${PUID:-314}
PGID=${PGID:-314}

groupmod -o -g "$PGID" titlecardmaker
usermod -o -u "$PUID" titlecardmaker

chown -R titlecardmaker:titlecardmaker /maker

exec gosu titlecardmaker "$@"