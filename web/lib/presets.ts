// SPDX-License-Identifier: AGPL-3.0-or-later
// The Jagannatha Hora reference charts used by the engine's golden tests.
import { Birth } from "./api";

export const PRESETS: { name: string; birth: Birth }[] = [
  { name: "Mahatma Gandhi", birth: { local_datetime: "1869-10-02T07:20:00", latitude: 21.6167, longitude: 69.8167, utc_offset_hours: 4.654444 } },
  { name: "Sri Aurobindo", birth: { local_datetime: "1872-08-15T05:17:00", latitude: 22.5, longitude: 88.3333, utc_offset_hours: 5.883333 } },
  { name: "Ramakrishna Paramhansa", birth: { local_datetime: "1836-02-18T06:44:00", latitude: 22.8833, longitude: 87.7333, utc_offset_hours: 5.85 } },
  { name: "B. V. Raman", birth: { local_datetime: "1912-08-08T19:38:00", latitude: 12.9833, longitude: 77.5833, utc_offset_hours: 5.5 } },
  { name: "Suryanarayan Rao", birth: { local_datetime: "1856-02-12T12:21:00", latitude: 18.0, longitude: 84.0, utc_offset_hours: 5.6 } },
  { name: "Maharshi Mahesh Yogi", birth: { local_datetime: "1917-01-12T08:50:00", latitude: 23.1667, longitude: 79.95, utc_offset_hours: 5.5 } },
  { name: "Sanjay Rath", birth: { local_datetime: "1963-08-07T21:15:40", latitude: 21.45, longitude: 83.9667, utc_offset_hours: 5.5 } },
  { name: "P. V. R. Narasimha Rao", birth: { local_datetime: "1970-04-04T17:50:40", latitude: 16.1667, longitude: 81.1333, utc_offset_hours: 5.5 } },
];
