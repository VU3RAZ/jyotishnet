# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Tiny X driver for Xvfb :77. usage: x.py shot FILE | key KEYSYM... | type TEXT | click X Y [right] | dbl X Y | wins"""
import os, sys, time
from Xlib import display, X, XK
from Xlib.ext import xtest
from PIL import Image
d = display.Display(os.environ.get("DISPLAY", ":77")); root = d.screen().root
def keysym(name):
    ks = XK.string_to_keysym(name)
    if not ks and len(name) == 1: ks = ord(name)
    return d.keysym_to_keycode(ks)
def press(combo):
    keys = [keysym(k) for k in combo.split("+")]
    for k in keys: xtest.fake_input(d, X.KeyPress, k)
    for k in reversed(keys): xtest.fake_input(d, X.KeyRelease, k)
    d.flush(); time.sleep(0.15)
SHIFT = set('~!@#$%^&*()_+{}|:"<>?ABCDEFGHIJKLMNOPQRSTUVWXYZ')
NAMES = {' ':'space','.':'period',',':'comma','-':'minus',':':'colon','/':'slash','\\':'backslash','_':'underscore','+':'plus','\n':'Return'}
def typ(text):
    for ch in text:
        name = NAMES.get(ch, ch)
        k = keysym(name)
        sh = ch in SHIFT
        if sh: xtest.fake_input(d, X.KeyPress, keysym('Shift_L'))
        xtest.fake_input(d, X.KeyPress, k); xtest.fake_input(d, X.KeyRelease, k)
        if sh: xtest.fake_input(d, X.KeyRelease, keysym('Shift_L'))
        d.flush(); time.sleep(0.03)
def click(x, y, button=1, n=1):
    xtest.fake_input(d, X.MotionNotify, x=x, y=y); d.flush(); time.sleep(0.1)
    for _ in range(n):
        xtest.fake_input(d, X.ButtonPress, button); xtest.fake_input(d, X.ButtonRelease, button); d.flush(); time.sleep(0.08)
    time.sleep(0.3)
cmd = sys.argv[1]
if cmd == "shot":
    g = root.get_geometry(); raw = root.get_image(0, 0, g.width, g.height, X.ZPixmap, 0xffffffff)
    Image.frombytes("RGB", (g.width, g.height), raw.data, "raw", "BGRX").save(sys.argv[2])
elif cmd == "key":
    for c in sys.argv[2:]: press(c)
elif cmd == "type": typ(sys.argv[2])
elif cmd == "click": click(int(sys.argv[2]), int(sys.argv[3]), 3 if len(sys.argv) > 4 else 1)
elif cmd == "dbl": click(int(sys.argv[2]), int(sys.argv[3]), 1, 2)
elif cmd == "wins":
    def walk(w, depth=0):
        for c in w.query_tree().children:
            try:
                n = c.get_wm_name(); a = c.get_attributes()
                if n and a.map_state == X.IsViewable:
                    g = c.get_geometry(); print(hex(c.id), repr(n), g.x, g.y, g.width, g.height)
            except Exception: pass
            walk(c, depth + 1)
    walk(root)
