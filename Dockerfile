# inspired from https://github.com/GoogleContainerTools/distroless/tree/main/examples/python3-requirements

FROM debian:12-slim AS build
RUN apt-get update && \
    apt-get install --no-install-suggests --no-install-recommends --yes python3-venv && \
    python3 -m venv /venv && \
    /venv/bin/pip install --upgrade pip setuptools wheel harbor_ls

FROM gcr.io/distroless/python3-debian12
COPY --from=build /venv /venv
ENTRYPOINT ["/venv/bin/python3", "-m", "harbor_ls"]
