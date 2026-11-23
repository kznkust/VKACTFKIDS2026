FROM ubuntu:22.04 AS builder
RUN apt-get update && apt-get install -y --no-install-recommends gcc libc6-dev \
    && rm -rf /var/lib/apt/lists/*
COPY seventh_face.c /src/seventh_face.c
RUN gcc -std=c11 -O0 -Wall -Wextra -fstack-protector-strong -fPIE -pie \
    -Wl,-z,relro,-z,now,-z,noexecstack /src/seventh_face.c -o /seventh_face

FROM ubuntu:22.04
RUN apt-get update && apt-get install -y --no-install-recommends socat coreutils \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --uid 10001 --no-create-home player
WORKDIR /app
COPY --from=builder /seventh_face /app/seventh_face
COPY flag.txt /app/flag.txt
RUN chown -R root:root /app && chmod 555 /app /app/seventh_face \
    && chmod 444 /app/flag.txt
USER player
EXPOSE 31337
CMD ["socat", "TCP-LISTEN:31337,reuseaddr,fork", "EXEC:timeout 60 /app/seventh_face,stderr"]
