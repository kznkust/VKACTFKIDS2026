FROM ubuntu:24.04
RUN apt-get update \
    && apt-get install -y --no-install-recommends socat \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -g 10001 player \
    && useradd -u 10001 -g 10001 -M -s /usr/sbin/nologin player
WORKDIR /app
COPY challenge /app/challenge
COPY flag.txt /app/flag.txt
RUN chmod 0555 /app/challenge && chmod 0444 /app/flag.txt
USER 10001:10001
EXPOSE 31337
CMD ["socat", "TCP-LISTEN:31337,reuseaddr,fork,max-children=48", "EXEC:/app/challenge,stderr"]
