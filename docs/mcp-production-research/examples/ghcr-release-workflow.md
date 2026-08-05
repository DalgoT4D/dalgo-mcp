# Example: publish a container image to GHCR on tag

dalgo-mcp builds its image only locally — a hosted/self-host server needs a published,
versioned image. This GitHub Actions workflow pushes to GHCR on every `v*` tag.

```yaml
# .github/workflows/docker.yml
name: Publish Docker image
on:
  push:
    tags: ["v*"]
jobs:
  docker:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write   # push to GHCR
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/metadata-action@v5
        id: meta
        with:
          images: ghcr.io/dalgot4d/dalgo-mcp
          tags: |
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=raw,value=latest
      - uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

## Notes
- Mirrors what GitHub (`ghcr.io/github/github-mcp-server`) and Grafana
  (`grafana/mcp-grafana`) publish.
- Add a Docker `HEALTHCHECK` to the image so orchestrators can probe `/health`.
- For k8s shops, follow with a Helm chart (Grafana ships one).
- Runs alongside the existing `publish.yml` (PyPI) — one tag, both artifacts.
```
