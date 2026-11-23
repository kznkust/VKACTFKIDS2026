#!/usr/bin/env python3

import argparse
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
import http.client
from http.cookies import SimpleCookie
import json
import secrets
import sys
import threading
import time
import urllib.error
import urllib.request

MODULUS = 2**31 - 1
CARDS = tuple(rank + suit for suit in "CDHS" for rank in "JQKA")


def decode(deck):
    remaining = list(CARDS)
    ticket = 0
    weight = 1
    for card in deck:
        index = remaining.index(card)
        ticket += index * weight
        weight *= len(remaining)
        remaining.pop(index)
    return ticket


def encode(ticket):
    remaining = list(CARDS)
    deck = []
    while remaining:
        ticket, index = divmod(ticket, len(remaining))
        deck.append(remaining.pop(index))
    return deck


class ApiClient:
    """Bounded retries with a stable table ID and round-based move recovery."""

    def __init__(self, base_url, timeout=5, hedge_delay=0.8, attempts=20,
                 progress=None):
        if timeout <= 0 or hedge_delay <= 0 or attempts < 1:
            raise ValueError("timeout, hedge_delay and attempts must be positive")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.hedge_delay = hedge_delay
        self.attempts = attempts
        self.progress = progress or (lambda message: None)
        self.cookie = None
        self.lock = threading.Lock()
        self.pool = ThreadPoolExecutor(max_workers=6)

    def once(self, path, message=None):
        headers = {"Content-Type": "application/json"}
        with self.lock:
            if self.cookie is not None:
                headers["Cookie"] = self.cookie
        request = urllib.request.Request(self.base_url + path,
            data=json.dumps(message).encode() if message is not None else None,
            headers=headers)
        opener = urllib.request.build_opener()
        try:
            response = opener.open(request, timeout=self.timeout)
        except urllib.error.HTTPError as error:
            status = error.code
            error.close()
            if status == 409 and path == "/api/guess":
                current = self.once("/api/state")
                if current.get("wins", -1) >= message["round"] or current.get("status") == "lost":
                    return current
            if status >= 500:
                raise OSError(f"Server returned HTTP {status}") from None
            raise RuntimeError(f"{path}: HTTP {status}") from None
        with response:
            cookie = SimpleCookie()
            cookie.load(response.headers.get("Set-Cookie", ""))
            if "dealer" in cookie:
                with self.lock:
                    self.cookie = "dealer=" + cookie["dealer"].value
            return json.load(response)

    def post(self, path, message):
        if path == "/api/new":
            message = dict(message, request_id=secrets.token_hex(16))
        def attempt(recover=False):
            if recover and path == "/api/guess":
                try:
                    current = self.once("/api/state")
                    if current.get("wins", -1) >= message["round"] or current.get("status") == "lost":
                        return current
                except (OSError, urllib.error.URLError, http.client.HTTPException,
                        json.JSONDecodeError):
                    pass
            return self.once(path, message)

        pending = {self.pool.submit(attempt)}
        launched = 1
        limit = self.attempts
        next_attempt = time.monotonic() + self.hedge_delay
        last_error = None
        try:
            while pending:
                timeout = max(0, next_attempt - time.monotonic()) if launched < limit else None
                done, pending = wait(pending, timeout=timeout, return_when=FIRST_COMPLETED)
                for future in done:
                    try:
                        return future.result()
                    except (OSError, urllib.error.URLError, http.client.HTTPException,
                            json.JSONDecodeError) as error:
                        last_error = error
                if launched < limit and (not pending or time.monotonic() >= next_attempt):
                    self.progress(f"{path}: retry {launched + 1}/{limit}")
                    pending.add(self.pool.submit(attempt, True))
                    launched += 1
                    next_attempt = time.monotonic() + self.hedge_delay
            raise RuntimeError(f"{path}: no response after {limit} attempts "
                               f"({type(last_error).__name__}: {last_error}); "
                               "check connectivity or increase --attempts / --timeout") from last_error
        finally:
            for future in pending:
                future.cancel()

    def close(self):
        self.pool.shutdown(wait=False, cancel_futures=True)


def solve(base_url, *, timeout=5, attempts=20, progress=None):
    client = ApiClient(base_url, timeout=timeout, attempts=attempts, progress=progress)
    try:
        return play(client)
    finally:
        client.close()


def play(client):
    client.progress("Starting game...")
    game = client.post("/api/new", {})
    x1, x2, x3 = map(decode, game["practice"])
    a = (x3 - x2) * pow((x2 - x1) % MODULUS, -1, MODULUS) % MODULUS
    c = (x2 - a * x1) % MODULUS
    state = x3
    for number in range(1, game["rounds"] + 1):
        if game.get("round") != number:
            raise RuntimeError(f"Unexpected round: {game}")
        state = (a * state + c) % MODULUS
        game = client.post("/api/guess", {"round": number, "cards": encode(state)[:5]})
        if game.get("wins") != number or game.get("status") == "lost":
            raise RuntimeError(f"Prediction failed: {game}")
        client.progress(f"Round {number}/{game['rounds']}: OK")
    if game.get("status") != "won":
        raise RuntimeError(f"Unexpected final state: {game}")
    return game["flag"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url", nargs="?", default="http://85.143.218.153:8080")
    parser.add_argument("--timeout", type=float, default=5,
                        help="socket timeout in seconds (default: 5)")
    parser.add_argument("--attempts", type=int, default=20,
                        help="attempts per operation (default: 20)")
    parser.add_argument("--quiet", action="store_true", help="only print the flag")
    args = parser.parse_args()
    if args.timeout <= 0 or args.attempts < 1:
        parser.error("--timeout and --attempts must be positive")
    try:
        print(solve(args.url, timeout=args.timeout, attempts=args.attempts,
                    progress=None if args.quiet else
                    lambda message: print(message, file=sys.stderr, flush=True)))
    except (RuntimeError, OSError, urllib.error.URLError) as error:
        parser.exit(1, f"Error: {error}\n")
