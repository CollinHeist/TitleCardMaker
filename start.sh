#!/bin/bash

PUID=${PUID:-99}
PGID=${PGID:-100}
UMASK=${UMASK:-002}

umask $UMASK
groupmod -o -g "$PGID" titlecardmaker
usermod -o -u "$PUID" titlecardmaker

chown -R titlecardmaker:titlecardmaker /maker /config

exec runuser -u titlecardmaker -g titlecardmaker -- "$@"