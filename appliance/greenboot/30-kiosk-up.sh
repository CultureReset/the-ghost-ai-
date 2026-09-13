#!/bin/bash
# The screen is the product. If it is not showing, the box has failed in
# front of everyone who works there.
set -euo pipefail
systemctl is-active --quiet ghost-kiosk.service
echo "kiosk running"
