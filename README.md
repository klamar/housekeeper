# housekeeper

Linux utility application that keeps directory structures clean. Auto-removal of old/unused files and directories.

## Configuration

Housekeeper reads all *.ini files in /etc/houskeeper

### Keep newest 3 files, remove all others

```
[backups]
type=keep
root=/data/backup/mybackup
match=*.tar.gz
keep=3
```
