# housekeeper

Linux utility application that keeps directory structures clean. Auto-removal of old/unused files and directories.

## Usage

Dry run:
```
#> housekeeper
my-backup-job: would remove: /data/backup/localhost.3.tar.gz
my-backup-job: would remove: /data/backup/localhost.4.tar.gz
my-backup-job: would remove: /data/backup/localhost.5.tar.gz
```

If you are happy with the results do the real run:
```
#> housekeeper -r
```

If you want to use housekeeper in a cron job, you can add the silent operator -s 
```
#> housekeeper -r -s
```

## Configuration

Housekeeper reads all *.ini files in /etc/houskeeper

### Remove files older than 1 week

Searches in /data/backup/mybackup recursively files matching *.tar.gz which are older than 1 week. Search goes only 3 directories deep.
```
[backups]
root=/data/backup/mybackup
match=*.tar.gz
older=1w
recurse=true
depth=3
```

### Keep newest 3 files, remove all others

Searches in /data/backup/mybackup files matching *.tar.gz, keeps the newest 3 files (mtime) and removes all others.
```
[backups]
type=keep
root=/data/backup/mybackup
match=*.tar.gz
keep=3
```

## Installation

### Requirements

* requires python2.7 (which is default on Debian 7 and Ubuntu 14.04 upwards)
* works with python2.6 when the argparse module is installed (Debian/Ubuntu package: python-argparse)

### Installation

* clone git repository somewhere
```
chmod a+x housekeeper.py
cp housekeeper /usr/local/bin/housekeeper
```
