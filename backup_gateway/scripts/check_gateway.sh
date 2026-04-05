#!/bin/bash
if systemctl is-active --quiet backup-gateway; then
    exit 0
else
    exit 1
fi
