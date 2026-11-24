# Exporting golden charts from Jagannatha Hora under Wine

How the edge-case charts in `tests/golden/jhora/` were made (November 2026),
without a Windows machine. JHora runs on a virtual X display, so the desktop is
not touched.

1. Install JHora 8.0 (`jh_full_install.exe`, Inno Setup) into its own prefix:

       export WINEPREFIX=/path/to/wine-jh
       Xvfb :77 -screen 0 1600x1000x24 -nolisten tcp &
       DISPLAY=:77 wine jh_full_install.exe /VERYSILENT /SUPPRESSMSGBOXES /DIR='C:\JHora'

2. Start JHora once and quit it (File > Exit) so it writes
   `C:\JHora\jhcore\jhora.ini`, then set the two values that differ from a
   fresh install and the golden set:

       UserSelectedAyanamsa=0    # Traditional Lahiri (fresh install: 17, True Lahiri/Chitrapaksha, 55" less)
       ChartStyle=2              # North Indian text charts, as the older exports

   With these, JHora's own sample "Author of this software" exports identically
   to `tests/golden/jhora/pvr_rao.txt` (apart from the file-path line). The
   other defaults already match: mean nodes, true positions, no refraction.

3. Write charts as `.jhd` files (see `tests/golden/jhd/`): one field per line,
   CRLF; month, day, year, time as h.mmss, zone as h.mmss (east negative),
   longitude as d.mmss (east negative), latitude as d.mmss (north positive),
   altitude, standard and summer zones in decimal hours (east negative), then
   `0 0 place country 1 1013.25 20 0`.

4. Export. Needs a Python with `python-xlib` and `pillow`:

       JH_PREFIX=$WINEPREFIX PY=/path/to/python DISPLAY_JH=:77 \
         tools/jhora/export.sh tests/golden/jhd /tmp/exports

   For each chart, `export.sh` opens it (JHora takes the file on its command
   line), clicks Edit > Copy complete calculations and reads the X clipboard.
   Clicks use screen positions for a 1600x1000 display.

Shadbala tables (the `jhora_shadbala` format) come from the Strengths tab >
Other strengths: right-click the Shadbala table, pick "Shadbala Break-up" or
"Sthana Bala" or "Kaala Bala", then "Copy to clipboard".

`xdrive.py` also takes screenshots (`xdrive.py shot out.png`) for finding new
menu positions.
