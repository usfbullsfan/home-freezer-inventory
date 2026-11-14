/**
 * Known public hostnames.
 *
 * Both the current domain (thefreezer.xyz, expiring 2026-12-31) and its
 * replacement (freezer.wetpaws.dev) are listed so the frontend behaves the
 * same on either while they run side by side. Remove the legacy entries once
 * thefreezer.xyz is retired.
 */
export const DEV_HOSTNAMES = [
  'dev.thefreezer.xyz',       // legacy
  'd-freezer.wetpaws.dev',
  'localhost',
  '127.0.0.1',
];

export const isDevHostname = (hostname = window.location.hostname) =>
  DEV_HOSTNAMES.includes(hostname);
