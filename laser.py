#!/usr/bin/env python3
from time import sleep
import os
import sys
import signal
import shlex
import math
import lirc

PY3 = sys.version_info[0] >= 3
if not PY3:
    print("Laser only works with `python3`.")
    sys.exit(1)

from threading import Barrier  # must be using Python 3
import subprocess
import pifacecommon
import pifacecad
from pifacecad.lcd import LCD_WIDTH

UPDATE_INTERVAL = 1

class Laser(object):
    def __init__(self, cad, hits=0):

        # set up cad
        cad.lcd.blink_off()
        cad.lcd.cursor_off()
        cad.lcd.backlight_on()

        self.cad = cad
        self._hits = hits

        self.cad.lcd.set_cursor(1, 0)
        self.cad.lcd.write("Welcome")
        self.cad.lcd.set_cursor(1, 1)
        self.cad.lcd.write("Warrior!")

    @property
    def hits(self):
        return self._hits

    @hits.setter
    def hits(self, hits):
        self._hits = hits
        message = "Hit count %d" % (self._hits,)
        self.cad.lcd.clear()
        self.cad.lcd.set_cursor(1, 0)
        self.cad.lcd.write(message)

    def ir(self, code):
        if code == 1:
           self.hits = self.hits+1
        else:
           self.hits = self.hits-1

    def close(self):
        self.cad.lcd.clear()
        self.cad.lcd.backlight_off()
        os._exit(0)

    def switch(self, message):
        self.cad.lcd.clear()
        self.cad.lcd.set_cursor(1, 0)
        self.cad.lcd.write(message)
        
def laser_switch(event):
    global laser
    laser.switch("Bye!")
    laser.close()

def laser_ir(event):
    global laser
    #print("IR code %d" % int(event.ir_code))
    laser.ir(int(event.ir_code))


if __name__ == "__main__":

    cad = pifacecad.PiFaceCAD()
    global laser
    laser = Laser(cad)

    # listener cannot deactivate itself so we have to wait until it has
    # finished using a barrier.
    global end_barrier
    end_barrier = Barrier(2)

    # wait for button presses
    switchlistener = pifacecad.SwitchEventListener(chip=cad)
    switchlistener.register(7, pifacecad.IODIR_ON, laser_switch)

    irlistener = pifacecad.IREventListener(
        prog="laser",
        lircrc="~/.lircrc")
    irlistener.register("1", laser_ir)
    irlistener.register("2", laser_ir)
    
    switchlistener.activate()
    try:
        irlistener.activate()
    except lirc.InitError:
        print("Could not initialise IR, running without IR controls.")
        irlistener_activated = False
    else:
        irlistener_activated = True

    end_barrier.wait()  # wait unitl exit

    # exit
    laser.close()
    switchlistener.deactivate()
    if irlistener_activated:
        irlistener.deactivate()
