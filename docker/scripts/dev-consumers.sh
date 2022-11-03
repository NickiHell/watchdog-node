#!/bin/bash

set -o errexit
set -o nounset

. ./scripts/utils/graceful-exit.sh
. ./scripts/utils/prestart.sh

trap 'graceful_exit 60' TERM INT HUP
wait_db

BUS=metadata_manager.eventler:event_bus

eventler -A $BUS consumer -s show-events-subscription &
eventler -A $BUS consumer -s rating-source-events-subscription &
eventler -A $BUS consumer -s rating-events-subscription &
eventler -A $BUS consumer -s person-events-subscription &
eventler -A $BUS consumer -s staff-events-subscription &
eventler -A $BUS consumer -s genre-subscription &
eventler -A $BUS consumer -s tag-subscription &
eventler -A $BUS consumer -s country-subscription

wait
