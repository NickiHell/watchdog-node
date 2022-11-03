#!/bin/bash

set -o errexit
set -o nounset

. ./scripts/utils/start-gunicorn.sh

start_gunicorn
