#!/bin/sh

set -eu

base=/usr/lib/vidbee
"$base/node/bin/node" "$base/api/dist/migrate-history.js"
exec "$base/node/bin/node" "$base/api/dist/index.js"
