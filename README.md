# waiter

A dead simple process manager.

Waiter runs a series of startup commands. It then waits until it recieves a
sigterm and then runs a series of shutdown commands. It is intended to be used
with tools such a firejail.

## Why?

firejail terminates when the parent pid exits. Therefore running script that
fork children and exit will cause the namespace jail to be torn down.

## Configuration

```
[program:seafile]
start = seafile.sh start
stop = seafile.sh stop

[program:seahub]
start = seahub.sh start-fastcgi
stop  = seahub.sh stop
```

## Examples
### Seafile

Standalone Command
```
firejail -- /usr/bin/waiter.py -c seafile.conf
```

/etc/systemd/system/seafile.service
```
[Unit]
Description=Seafile
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/firejail --profile=/etc/firejail/server.profile --name=seafile -- waiter.py -c /etc/waiter/seafile.conf
ExecStop=/usr/bin/firejail --shutdown=${MAINPID}

[Install]
WantedBy=multi-user.target
```
