# Jagannatha Hora golden set

Charts entered by hand in Jagannatha Hora (JHora), with its outputs transcribed
here. They are the final authority when the engine and PyJHora disagree.

Target: 50 charts chosen for edge cases (design doc, Layer 0 verification):

- planets within 0.1 deg of a sign or nakshatra boundary
- high latitudes (Srinagar, Leh) and the far south (Kanyakumari)
- pre-1955 Indian time zones and war time (1942-45)
- southern-hemisphere and western-hemisphere births

## How to add a chart

Add an object to `jhora_golden.json`:

```json
{
  "id": "delhi-1990-01-15",
  "note": "Why this chart is an edge case",
  "birth": {"local_datetime": "1990-01-15T06:30:00", "latitude": 28.61,
            "longitude": 77.21, "utc_offset_hours": 5.5},
  "config": {"ayanamsa": "lahiri", "node_type": "mean", "true_positions": false},
  "expect": {
    "longitudes": {"La": 258.349, "Su": 270.896},
    "vargas": {"9": {"La": 5, "Su": 9}},
    "vimshottari_md": [{"lord": "Ve", "end": "2003-01-02"}]
  },
  "tolerance_deg": 0.01
}
```

Signs are 0-11 from Aries. Only fill in the fields you transcribed; the test
checks whatever is present. Record the JHora settings used (ayanamsa, node
type, true or apparent positions, year length) in `config`.
