#!/bin/sh
# usage: urlhead.sh URL...
# reads the HEAD of each URL: final status, size, final url
for u; do
  curl -sL -o /dev/null -I -m 25 -w "%{http_code}\t%header{content-length}\t%{url_effective}\n" "$u" || echo "ERR\t-\t$u"
done
