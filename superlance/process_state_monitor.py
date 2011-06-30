#!/usr/bin/env python -u
##############################################################################
#
# Copyright (c) 2007 Agendaless Consulting and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the BSD-like license at
# http://www.repoze.org/LICENSE.txt.  A copy of the license should accompany
# this distribution.  THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL
# EXPRESS OR IMPLIED WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND
# FITNESS FOR A PARTICULAR PURPOSE
#
##############################################################################
doc = """\
Base class for common functionality when monitoring process state changes
"""

import os
import sys

from supervisor import childutils

class ProcessStateMonitor:

    # In child class, define a list of events to monitor
    processStateEvents = []

    def __init__(self, **kwargs):
        self.interval = kwargs.get('interval', 1.0)
        
        self.debug = kwargs.get('debug', False)
        self.stdin = kwargs.get('stdin', sys.stdin)
        self.stdout = kwargs.get('stdout', sys.stdout)
        self.stderr = kwargs.get('stderr', sys.stderr)
        self.eventname = kwargs.get('eventname', 'TICK_60')
        self.tickmins = self._get_tick_mins(self.eventname)
        
        self.batchMsgs = []
        self.batchMins = 0.0

    def _get_tick_mins(self, eventname):
        return float(self._get_tick_secs(eventname))/60.0

    def _get_tick_secs(self, eventname):
        self._validate_tick_name(eventname)
        return int(eventname.split('_')[1])
        
    def _validate_tick_name(self, eventname):
        if not eventname.startswith('TICK_'):
            raise ValueError("Invalid TICK event name: %s" % eventname)
 
    def run(self):
        while 1:
            hdrs, payload = childutils.listener.wait(self.stdin, self.stdout)
            self.handleEvent(hdrs, payload)
            childutils.listener.ok(self.stdout)
    
    def handleEvent(self, headers, payload):
        if headers['eventname'] in self.processStateEvents:
            self.handleProcessStateChangeEvent(headers, payload)
        elif headers['eventname'] == self.eventname:
            self.handleTickEvent(headers, payload)
    
    def handleProcessStateChangeEvent(self, headers, payload):
        msg = self.getProcessStateChangeMsg(headers, payload)
        if msg:
            self.writeToStderr('%s\n' % msg)
            self.batchMsgs.append(msg)

    """
    Override this method in child classes to customize messaging
    """
    def getProcessStateChangeMsg(self, headers, payload):
        return None

    def handleTickEvent(self, headers, payload):
        self.batchMins += self.tickmins
        if self.batchMins >= self.interval:
            self.sendBatchNotification()
            self.clearBatch()
            
    """
    Override this method in child classes to send notification
    """
    def sendBatchNotification(self):
        pass
    
    def getBatchMinutes(self):
        return self.batchMins
    
    def getBatchMsgs(self):
        return self.batchMsgs
        
    def clearBatch(self):
        self.batchMins = 0.0;
        self.batchMsgs = [];

    def writeToStderr(self, msg):
        self.stderr.write(msg)
        self.stderr.flush()