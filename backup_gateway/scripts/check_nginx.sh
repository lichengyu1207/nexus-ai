#!/bin/bash
if pgrep -x nginx > /dev/null; then
    exit 0
else
    exit 1
fi
