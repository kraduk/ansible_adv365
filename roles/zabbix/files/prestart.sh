#!/bin/sh
echo "Hostname="`hostname| tr 'A-Z' 'a-z'` > /etc/zabbix/agentd.conf.d/host.conf
/sbin/ip addr show mgmt | awk '/ inet / { gsub(/\/[0-9]+$/,"",$2); print "ListenIP="$2}' > /etc/zabbix/agentd.conf.d/listen.conf
/usr/sbin/zabbix_agentd -c /etc/zabbix/agentd.conf


