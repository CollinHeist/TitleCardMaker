# https://github.com/UnRAIDES/unRAID-NerdTools/pull/84

mkdir /tmp/build-python3.12/
cd /tmp/build-python3.12/

wget https://slackware.uk/slackware/slackware64-current/slackware64/d/pkg-config-0.29.2-x86_64-4.txz
installpkg pkg-config-0.29.2-x86_64-4.txz

wget https://slackware.uk/slackware/slackware64-current/slackware64/d/gcc-13.2.0-x86_64-1.txz
installpkg gcc-13.2.0-x86_64-1.txz

wget https://slackware.uk/slackware/slackware64-current/slackware64/l/glibc-2.39-x86_64-1.txz
installpkg glibc-2.39-x86_64-1.txz

wget https://slackware.uk/slackware/slackware64-current/slackware64/d/binutils-2.42-x86_64-1.txz
installpkg binutils-2.42-x86_64-1.txz

wget https://slackware.uk/slackware/slackware64-current/slackware64/d/make-4.4.1-x86_64-1.txz
installpkg make-4.4.1-x86_64-1.txz

wget https://slackware.uk/slackware/slackware64-current/slackware64/d/guile-3.0.9-x86_64-1.txz
installpkg guile-3.0.9-x86_64-1.txz

wget https://slackware.uk/slackware/slackware64-current/slackware64/l/gc-8.2.6-x86_64-1.txz
installpkg gc-8.2.6-x86_64-1.txz

wget https://slackware.uk/slackware/slackware64-current/slackware64/l/libunistring-1.2-x86_64-1.txz
installpkg libunistring-1.2-x86_64-1.txz

wget https://slackware.uk/slackware/slackware64-current/slackware64/l/zlib-1.3.1-x86_64-1.txz
installpkg zlib-1.3.1-x86_64-1.txz

wget https://slackware.uk/slackware/slackware64-current/slackware64/l/libffi-3.4.6-x86_64-1.txz
installpkg libffi-3.4.6-x86_64-1.txz

wget https://slackware.uk/slackware/slackware64-current/slackware64/n/openssl-3.2.1-x86_64-1.txz
installpkg openssl-3.2.1-x86_64-1.txz

wget https://slackware.uk/slackware/slackware64-current/slackware64/a/bzip2-1.0.8-x86_64-3.txz
installpkg bzip2-1.0.8-x86_64-3.txz

wget https://slackware.uk/slackware/slackware64-current/slackware64/a/xz-5.6.0-x86_64-1.txz
installpkg xz-5.6.0-x86_64-1.txz

wget https://slackware.uk/slackware/slackware64-current/slackware64/l/gdbm-1.23-x86_64-2.txz
installpkg gdbm-1.23-x86_64-2.txz

wget https://slackware.uk/slackware/slackware64-current/slackware64/l/ncurses-6.4_20230610-x86_64-1.txz
installpkg ncurses-6.4_20230610-x86_64-1.txz

wget https://slackware.uk/slackware/slackware64-current/slackware64/ap/sqlite-3.45.1-x86_64-1.txz
installpkg sqlite-3.45.1-x86_64-1.txz

wget https://www.python.org/ftp/python/3.12.2/Python-3.12.2.tar.xz
tar xf Python-3.12.2.tar.xz
cd Python-3.12.2

./configure --build=x86_64-slackware-linux --enable-loadable-sqlite-extensions --with-ensurepip=upgrade --prefix=/usr --libdir=/usr/lib64 --with-platlibdir=lib64 --enable-optimizations --with-pkg-config=yes --disable-test-modules --without-static-libpython

make -j6

mkdir -p /tmp/package-python-make-output
make install DESTDIR=/tmp/package-python-make-output

cd /tmp/package-python-make-output/
find . \( -name '*.exe' -o -name '*.bat' \) -exec rm -f '{}' \+
find . -type d -exec chmod 755 "{}" \+
find . -perm 640 -exec chmod 644 "{}" \+
find . -perm 750 -exec chmod 755 "{}" \+
find . -print0 | xargs -0 file | grep -e "executable" -e "shared object" | grep ELF  | cut -f 1 -d : | xargs strip --strip-unneeded 2> /dev/null || true
strip -s usr/lib/* usr/lib64/* usr/bin/*

mkdir install && cd install && wget https://www.slackbuilds.org/slackbuilds/14.2/python/python3/slack-desc
cd /tmp/package-python-make-output && /sbin/makepkg -l y -c n /tmp/python3-3.12.2-x86_64-1.txz
installpkg /tmp/python3-3.12.2-x86_64-1.txz
