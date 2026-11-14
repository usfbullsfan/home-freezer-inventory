/**
 * Known public hostnames.
 */
export const DEV_HOSTNAMES = [
  'dfreezer.wetpaws.dev',
  'localhost',
  '127.0.0.1',
];

export const isDevHostname = (hostname = window.location.hostname) =>
  DEV_HOSTNAMES.includes(hostname);
