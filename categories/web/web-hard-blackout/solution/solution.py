#!/usr/bin/env python3
import argparse
import hashlib
import json
import re
from collections import deque
from urllib.error import HTTPError
from urllib.request import Request, urlopen

LANES, WORD = 13, 8


def fetch(url, method="GET", headers=None, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    request = Request(url, data=data, method=method, headers=headers or {})
    if data is not None:
        request.add_header("Content-Type", "application/json")
    try:
        result = urlopen(request, timeout=10)
    except HTTPError as failure:
        if failure.code != 304:
            raise
        result = failure
    with result:
        return result.code, result.headers, result.read()


def edition(base_url, path, language):
    headers = {"Accept-Language": language}
    _, head, _ = fetch(base_url + path, "HEAD", headers)
    tag = head["ETag"]
    code, metadata, _ = fetch(base_url + path, headers=headers | {"If-None-Match": tag})
    if code != 304:
        raise ValueError("Expected an archive receipt on 304")
    target_path = re.fullmatch(r'<([^>]+)>; rel="derived-from"', metadata["Link"]).group(1)
    if target_path.rsplit("/", 1)[0] != path.rsplit("/", 1)[0]:
        raise ValueError("Archive link leaves the current case")
    fragments = []
    for interval in metadata["X-Undertow-Fragments"].split(","):
        code, _, fragment = fetch(base_url + path, headers=headers | {
            "If-Range": tag,
            "Range": f"bytes={interval}",
        })
        if code != 206 or len(fragment) != 52:
            raise ValueError("Broken byte range")
        fragments.append(fragment)
    return target_path, int(metadata["X-Undertow-Shift"]), b"".join(fragments)


def read_graph(base_url, first):
    pending = deque([first])
    graph = {}
    while pending:
        path = pending.popleft()
        if path in graph:
            continue
        graph[path] = [edition(base_url, path, language) for language in ("en", "fr")]
        pending.extend(target for target, _, _ in graph[path] if target not in graph)
    if len(graph) != 17:
        raise ValueError("Archive is incomplete")
    return graph


def rotate(data, shift):
    offset = (shift % LANES) * WORD
    return data[offset:] + data[:offset]


def xor(left, right):
    return bytes(a ^ b for a, b in zip(left, right, strict=True))


def reconstruct(graph, first, reference):
    transforms = {first: (0, bytes(LANES * WORD))}
    pending = deque([first])
    closure = None
    while pending:
        path = pending.popleft()
        shift, mask = transforms[path]
        for target, step, delta in graph[path]:
            candidate_shift = (shift - step) % LANES
            candidate_mask = rotate(xor(mask, delta), -step)
            if target not in transforms:
                transforms[target] = candidate_shift, candidate_mask
                pending.append(target)
                continue
            known_shift, known_mask = transforms[target]
            cycle_shift = (candidate_shift - known_shift) % LANES
            if cycle_shift:
                closure = cycle_shift, rotate(xor(candidate_mask, known_mask), -known_shift)
    if closure is None or len(transforms) != len(graph):
        raise ValueError("Missing a full orbit for the reference lane")

    cycle_shift, delta = closure
    lane = reference["lane"]
    value = bytes.fromhex(reference["value"])
    anchor = value
    root = bytearray(LANES * WORD)
    for _ in range(LANES):
        offset = lane * WORD
        root[offset:offset + WORD] = value
        value = xor(value, delta[offset:offset + WORD])
        lane = (lane + cycle_shift) % LANES
    if value != anchor:
        raise ValueError("Reference orbit is inconsistent")

    stripes = {path: xor(rotate(root, shift), mask) for path, (shift, mask) in transforms.items()}
    for path, edges in graph.items():
        for other, step, delta in edges:
            if stripes[path] != xor(rotate(stripes[other], step), delta):
                raise ValueError("Recovered stripes do not satisfy all editions")
    return hashlib.sha256(b"".join(stripes[path] for path in sorted(stripes))).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("base_url")
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/")
    _, _, body = fetch(base_url + "/api/case", "POST", payload={})
    case = json.loads(body)
    graph = read_graph(base_url, case["entry"])
    answer = reconstruct(graph, case["entry"], case["reference"])
    _, _, result = fetch(base_url + "/api/submit", "POST", payload={"case": case["case"], "answer": answer})
    print(json.loads(result)["flag"])


if __name__ == "__main__":
    main()
