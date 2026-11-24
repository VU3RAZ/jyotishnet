# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Print the CLIPBOARD selection of :77 as text."""
import os, sys, time
from Xlib import display, X
d = display.Display(os.environ.get("DISPLAY", ":77"))
w = d.screen().root.create_window(0, 0, 1, 1, 0, X.CopyFromParent)
CLIP = d.intern_atom("CLIPBOARD"); PROP = d.intern_atom("JHCLIP")
for tname in ("UTF8_STRING", "STRING", "TEXT"):
    t = d.intern_atom(tname)
    w.convert_selection(CLIP, t, PROP, X.CurrentTime); d.flush()
    end = time.time() + 5
    while time.time() < end:
        if d.pending_events():
            e = d.next_event()
            if e.type == X.SelectionNotify:
                if e.property == X.NONE: break
                r = w.get_full_property(PROP, X.AnyPropertyType, sizehint=10_000_000)
                data = r.value if r else b""
                if isinstance(data, str): data = data.encode("latin1")
                sys.stdout.buffer.write(bytes(data)); sys.exit(0)
        else: time.sleep(0.05)
sys.exit(1)
