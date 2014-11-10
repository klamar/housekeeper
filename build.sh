#!/bin/sh

mkdir -p $PACKAGE_LIB/usr/bin
mkdir -p $PACKAGE_LIB/etc/cron.daily
mkdir -p $PACKAGE_LIB/etc/housekeeper

cp housekeeper.py $PACKAGE_LIB/usr/bin/housekeeper

dos2unix $PACKAGE_LIB/usr/bin/housekeeper

chmod a+x $PACKAGE_LIB/usr/bin/housekeeper

cat > $PACKAGE_LIB/etc/cron.daily/housekeeper <<EOF
#!/bin/bash
housekeeper -s -r
EOF

chmod a+x $PACKAGE_LIB/etc/cron.daily/housekeeper
