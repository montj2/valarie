#!/bin/bash

VALARIED_DIR=/var/dcs_share/valarie
PIDFILE=$VALARIED_DIR/pid
SERVICE=valaried

#RESTART VALARIE PROCESS"
if [ -e $PIDFILE ]; then
  /etc/init.d/$SERVICE stop > /dev/null
  /etc/init.d/$SERVICE start > /dev/null
fi

