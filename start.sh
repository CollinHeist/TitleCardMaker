#!/user/bin/env bash

PUID=${PUID:-314}
PGID=${PGID:-314}

groupmod -o -g "$PGID" titlecardmaker
usermod -o -u "$PUID" titlecardmaker

find /maker \! \( -uid $(id -u titlecardmaker) -gid $(id -g titlecardmaker) \) -print0 | xargs -0r chown titlecardmaker:titlecardmaker

exec gosu titlecardmaker "$@"