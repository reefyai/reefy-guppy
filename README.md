# reefy-guppy

Tiny HTTP test app for [Reefy](https://reefy.ai) devices. Used by the
golden-path e2e suite (`reefyai/reefy-service:tests/e2e/`) as the
generic "any app" install target.

## What's in the image

- `python:3.12-alpine` base
- `server.py` - small HTTP server on `:8080` returning device info
  (uptime, mem, load, disk for `/config`).
- `openssh-sftp-server` so the device's per-app SSH ForceCommand
  (`ssh app-<name>@host`) can route sftp/modern-scp through
  `docker exec sftp-server` inside the container.

## Build

GHA workflow (`.github/workflows/build.yml`) runs on every push to
`main` (when Dockerfile/server.py change) and on `workflow_dispatch`.
Tag format: `ghcr.io/reefyai/reefy-guppy:<YYYY.MM.DD>-<run_number>` +
`latest`.

## Pinning from reefy-service

Edit `apps/guppy/app.json` `image:` to a specific tag. The e2e suite
picks up whatever `apps/guppy/app.json` says.
