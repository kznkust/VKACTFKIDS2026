#!/usr/bin/env python3
import argparse
import csv
import hashlib
import json
import struct
from collections import deque
from functools import cache
from itertools import product
from pathlib import Path
from urllib.request import Request, urlopen

DIRECTIONS = (
    (1, 0, 0), (0, 1, 0), (0, 0, 1),
    (1, 1, 0), (1, -1, 0), (1, 0, 1), (1, 0, -1),
    (0, 1, 1), (0, 1, -1), (1, 1, 1), (1, 1, -1),
    (1, -1, 1), (1, -1, -1), (1, 2, 0), (1, 0, -2), (1, -2, 1), (0, 1, 2),
)


def read_export(data):
    if len(data) < 6 or data[:4] != b"VCT2" or data[4] != 16:
        raise ValueError("Expected a VCT2 export with a 16-cube")
    cursor = 6
    scans = []
    for _ in range(data[5]):
        marker = data[cursor:cursor + 4].hex()
        width, height = data[cursor + 4:cursor + 6]
        cursor += 6
        row_struct = struct.Struct(f"<{2 * width + 1}h")
        jig, readings = [], []
        for row in range(height):
            dark, *optical = row_struct.unpack_from(data, cursor)
            cursor += row_struct.size
            guide, cargo = optical[:width], optical[width:]
            if row % 2:
                guide, cargo = guide[::-1], cargo[::-1]
            jig.append(tuple(value - dark for value in guide))
            readings.append(tuple(value - dark if value != 0x7fff else None for value in cargo))
        scans.append((marker, tuple(jig), readings))
    if cursor != len(data):
        raise ValueError("Unexpected trailer in scan file")
    return scans


@cache
def make_rays(size, direction):
    coordinates = list(product(range(size), repeat=3))
    pivot = next(i for i, step in enumerate(direction) if step)
    axes = [axis for axis in range(3) if axis != pivot]
    intersections = [tuple(p[axis] - direction[axis] * p[pivot] for axis in axes)
                     for p in coordinates]
    min_u = min(u for u, _ in intersections)
    min_v = min(v for _, v in intersections)
    width = max(u for u, _ in intersections) - min_u + 1
    height = max(v for _, v in intersections) - min_v + 1
    rays = [[[] for _ in range(width)] for _ in range(height)]
    for voxel, (u, v) in enumerate(intersections):
        rays[v - min_v][u - min_u].append(voxel)
    return rays


def rotations(board):
    for reflection in (False, True):
        image = [row[::-1] for row in board] if reflection else board
        for _ in range(4):
            yield image
            image = list(zip(*reversed(image), strict=True))


def identify(scans, points, size):
    reference_bits = {x * size ** 2 + y * size + z for x, y, z in points}
    signatures = {}
    for direction in DIRECTIONS:
        for rays in rotations(make_rays(size, direction)):
            signature = tuple(tuple(sum(voxel in reference_bits for voxel in ray) for ray in row)
                              for row in rays)
            signatures.setdefault(signature, []).append((direction, rays))

    constraints = []
    used = set()
    for marker, signature, cargo in scans:
        candidates = signatures.get(signature, [])
        if len(candidates) != 1:
            raise ValueError(f"Expected one matching mounting for detector {marker}")
        direction, rays = candidates[0]
        if direction in used:
            raise ValueError(f"Detector direction {direction} appears twice")
        used.add(direction)
        for targets, row in zip(cargo, rays, strict=True):
            constraints.extend((ray, value) for ray, value in zip(row, targets, strict=True)
                               if value is not None)
    return constraints


def reconstruct(size, constraints):
    bits = [None] * (size ** 3)
    related = [[] for _ in bits]
    remaining = [len(ray) for ray, _ in constraints]
    residue = [value for _, value in constraints]
    for row, (ray, _) in enumerate(constraints):
        for voxel in ray:
            related[voxel].append(row)
    queue = deque(range(len(constraints)))
    while queue:
        row = queue.popleft()
        left, count = remaining[row], residue[row]
        if not 0 <= count <= left:
            raise ValueError("The scan constraints contradict each other")
        if left == 0 or count not in (0, left):
            continue
        fill = int(count == left)
        for voxel in constraints[row][0]:
            if bits[voxel] is not None:
                continue
            bits[voxel] = fill
            for other in related[voxel]:
                remaining[other] -= 1
                residue[other] -= fill
                queue.append(other)
    if None in bits:
        raise ValueError(f"Undetermined voxels: {bits.count(None)}")
    volume = bytes(bits)
    if any(sum(volume[i] for i in ray) != total for ray, total in constraints):
        raise ValueError("Reconstructed volume fails ray verification")
    return volume


def declaration(volume, size):
    digest = hashlib.sha256(volume).hexdigest()
    air = {point for point, solid in zip(product(range(size), repeat=3), volume, strict=True)
           if not solid}
    pockets = []
    while air:
        seed = min(air)
        air.remove(seed)
        queue = [seed]
        surface = False
        for point in queue:
            for axis, coordinate in enumerate(point):
                if coordinate in (0, size - 1):
                    surface = True
                for sign in (-1, 1):
                    neighbor = point[:axis] + (coordinate + sign,) + point[axis + 1:]
                    if neighbor in air:
                        air.remove(neighbor)
                        queue.append(neighbor)
        if not surface:
            pockets.append((-len(queue), seed))
    lines = [digest]
    for negative_count, (x, y, z) in sorted(pockets)[:3]:
        lines.append(f"{x},{y},{z}|{-negative_count}")
    return "\n".join(lines)


def solve(data, jig_file):
    with open(jig_file, newline="", encoding="utf-8") as file:
        points = [tuple(map(int, row)) for row in list(csv.reader(file))[1:]]
    scans = read_export(data)
    constraints = identify(scans, points, data[4])
    return declaration(reconstruct(data[4], constraints), data[4])


def post(base, path, payload):
    request = Request(base + path, data=json.dumps(payload).encode(), method="POST",
                      headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=15) as response:
        return json.load(response)


def solve_online(base, calibration):
    ticket = post(base, "/api/case", {})
    if ticket["data"] != f'/cargo/{ticket["case"]}/parcel.vct':
        raise ValueError("Unexpected detector export address")
    with urlopen(base + ticket["data"], timeout=15) as response:
        report = solve(response.read(), calibration)
    return post(base, "/api/submit", {"case": ticket["case"], "answer": report})["flag"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("export", type=Path, nargs="?")
    parser.add_argument("--url", help="solve a parcel on this challenge URL")
    parser.add_argument("--calibration", type=Path,
                        default=Path(__file__).resolve().parents[1] / "give/calibration.csv")
    args = parser.parse_args()
    if args.url and args.export is None:
        print(solve_online(args.url.rstrip("/"), args.calibration))
    elif args.export is not None and not args.url:
        print(solve(args.export.read_bytes(), args.calibration))
    else:
        parser.error("pass a VCT2 file or use --url")


if __name__ == "__main__":
    main()
