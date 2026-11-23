#!/usr/bin/env python3
import argparse
import binascii
import json
import sys
import wave
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.request import Request, urlopen

import numpy as np


def load_wav(path, rate):
    with wave.open(str(path), "rb") as wav:
        if (wav.getnchannels(), wav.getsampwidth(), wav.getframerate()) != (2, 2, rate):
            raise ValueError("Expected two PCM16 channels at the profile's sample rate")
        pcm = np.frombuffer(wav.readframes(wav.getnframes()), dtype="<i2").astype(float)
    return pcm.reshape((-1, 2)).T


def difference(left, right):
    def estimate(delay):
        a = left[:-delay]
        b = right[delay:]
        cross = np.dot(a, b)
        left_power = np.dot(a, a)
        right_power = np.dot(b, b)
        return cross / np.sqrt(left_power * right_power), cross / left_power

    correlation, delay, gain = max(
        (score, lag, scale) for lag in range(2, 12) for score, scale in [estimate(lag)]
    )
    if correlation < 0.8:
        raise ValueError("No delayed common signal in the channels")
    return right[delay:] - gain * left[:-delay], delay, gain


def basis(width, carrier_bin):
    return np.exp(2j * np.pi * carrier_bin * np.arange(width) / width)


def candidate_offsets(samples, tone, pilot, packet_samples):
    phases = np.exp(0.5j * np.pi * np.cumsum([0, *pilot]))
    template = (phases[:, None] * tone).reshape(-1)
    width = len(template)
    count = len(samples)
    if count < packet_samples:
        raise ValueError("Incomplete recording")
    padded = 1 << (count + width - 2).bit_length()
    product = np.fft.fft(samples, padded) * np.fft.fft(np.conj(template[::-1]), padded)
    match = np.abs(np.fft.ifft(product)[width - 1:count])
    power = np.r_[0., np.cumsum(samples ** 2)]
    score = match / np.sqrt(np.maximum(1., (power[width:] - power[:-width]) * width))
    peaks = np.flatnonzero(score[:count - packet_samples + 1] > .53)
    chosen = []
    for index in sorted((int(peak) for peak in peaks), key=lambda i: score[i], reverse=True):
        if all(abs(previous - index) > packet_samples // 2 for previous in chosen):
            chosen.append(index)
    return sorted(chosen)


def read_packet(samples, start, tone, pilot, turns, packet_bytes):
    symbol_samples = len(tone)
    count = 1 + len(pilot) + 4 * packet_bytes
    end = start + count * symbol_samples
    if start < 0 or end > len(samples):
        return None
    phases = samples[start:end].reshape((count, symbol_samples)) @ np.conj(tone)
    difference = np.angle(phases[1:] * np.conj(phases[:-1]))
    decoded = (np.rint(difference * 2 / np.pi).astype(int) % 4).tolist()
    if decoded[:len(pilot)] != pilot:
        return None
    dibits = [turns.index(phase) for phase in decoded[len(pilot):]]
    result = bytes(sum(part << shift for part, shift in zip(dibits[i:i+4], (6, 4, 2, 0), strict=True))
                   for i in range(0, len(dibits), 4))
    if binascii.crc_hqx(result[:-2], 0xFFFF) != int.from_bytes(result[-2:], "big"):
        return None
    return result


def coefficients(points, degree_count, modulus):
    if len(points) < degree_count:
        raise ValueError("Not enough independent valid frames")
    matrix = [[pow(x, degree, modulus) for degree in range(degree_count)] + y
              for x, y in sorted(points.items())[:degree_count]]
    for col in range(degree_count):
        pivot = next(row for row in range(col, degree_count) if matrix[row][col])
        matrix[col], matrix[pivot] = matrix[pivot], matrix[col]
        scale = pow(matrix[col][col], -1, modulus)
        matrix[col] = [(entry * scale) % modulus for entry in matrix[col]]
        for row in range(degree_count):
            if row == col:
                continue
            factor = matrix[row][col]
            matrix[row] = [(a - factor * b) % modulus for a, b in zip(matrix[row], matrix[col], strict=True)]
    values = [row[degree_count:] for row in matrix]
    for x, expected in points.items():
        for column, target in enumerate(expected):
            total = sum(pow(x, n, modulus) * row[column] for n, row in enumerate(values))
            if total % modulus != target:
                raise ValueError("Frames do not lie on the same set of polynomials")
    return bytes(value for row in values for value in row)


def restore(path, cfg, tag, verbose=False):
    left, right = load_wav(path, cfg["sample_rate"])
    samples, delay, gain = difference(left, right)
    width = cfg["symbol_samples"]
    tone = basis(width, cfg["carrier_bin"])
    pilot, turns = cfg["pilot_turns"], cfg["dibit_to_turn"]
    columns, modulus = cfg["columns"], cfg["field"]
    length = 5 + 2 * columns
    starts = candidate_offsets(samples, tone, pilot, (1 + len(pilot) + 4 * length) * width)
    points = {}
    valid = 0
    for start in starts:
        for adjustment in (0, -1, 1, -2, 2, -3, 3, -4, 4):
            packet = read_packet(samples, start + adjustment, tone, pilot, turns, length)
            if packet is None:
                continue
            valid += 1
            if packet[:2] == tag and packet[2]:
                data = packet[3:-2]
                points[packet[2]] = [int.from_bytes(data[i:i+2], "big") for i in range(0, len(data), 2)]
            break
    if verbose:
        print(f"delay={delay} gain={gain:.3f} bursts={len(starts)} crc_ok={valid} target={len(points)}",
              file=sys.stderr)
    return coefficients(points, cfg["coefficient_rows"], modulus)


def post(base, path, payload):
    request = Request(base + path, data=json.dumps(payload).encode(), method="POST",
                      headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=15) as response:
        return json.load(response)


def solve_online(base, cfg, verbose):
    ticket = post(base, "/api/case", {})
    if ticket["take"] != f'/takes/{ticket["case"]}/recording.wav':
        raise ValueError("Unexpected recording address")
    with urlopen(base + ticket["take"], timeout=15) as response, TemporaryDirectory() as tmp:
        path = Path(tmp) / "recording.wav"
        path.write_bytes(response.read())
        answer = restore(path, cfg, bytes.fromhex(ticket["callsign"]), verbose).hex()
    return post(base, "/api/submit", {"case": ticket["case"], "answer": answer})["flag"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("wav", nargs="?")
    parser.add_argument("callsign", nargs="?")
    parser.add_argument("--url", help="solve a live recording on this challenge URL")
    parser.add_argument("--profile", type=Path,
                        default=Path(__file__).resolve().parents[1] / "give/station-profile.json")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    with open(args.profile, encoding="utf-8") as profile:
        cfg = json.load(profile)
    if args.url and not (args.wav or args.callsign):
        print(solve_online(args.url.rstrip("/"), cfg, args.verbose))
    elif not args.url and args.wav and args.callsign:
        print(restore(args.wav, cfg, bytes.fromhex(args.callsign), args.verbose).hex())
    else:
        parser.error("pass a WAV and callsign, or use --url")


if __name__ == "__main__":
    main()
