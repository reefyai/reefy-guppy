# reefy-guppy: tiny test app for Reefy devices.
#
# Vendored to our org (vs. running raw `python:3.12-alpine`) so we can
# bake server.py + sftp-server into the image. The latter lets the
# device's per-app SSH ForceCommand route sftp/modern-scp through
# `docker exec sftp-server` inside this container - exercised by the
# golden_path e2e step 6s assertions.

FROM python:3.12-alpine

LABEL org.opencontainers.image.title="reefy-guppy" \
      org.opencontainers.image.description="Tiny HTTP test app for Reefy. Used by golden_path e2e." \
      org.opencontainers.image.licenses="MIT"

# openssh-sftp-server: provides /usr/lib/ssh/sftp-server, used by the
# device's reefy-app-shell when an SSH client (modern scp, Filezilla)
# requests the sftp subsystem.
RUN apk add --no-cache openssh-sftp-server

COPY server.py /app/server.py

EXPOSE 8080
CMD ["python3", "/app/server.py"]
