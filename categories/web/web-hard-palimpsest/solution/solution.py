#!/usr/bin/env python3
import argparse
import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.request import Request, urlopen

VOID = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
    "param", "source", "track", "wbr",
}


@dataclass(eq=False)
class Element:
    tag: str
    attrs: dict
    parent: object

    def ancestors(self):
        node = self.parent
        while node is not None:
            yield node
            node = node.parent


class Ward(HTMLParser):
    def __init__(self, page):
        super().__init__()
        self.elements = []
        self.stack = []
        self.feed(page)
        self.close()

    def handle_starttag(self, tag, attrs):
        node = Element(tag, dict(attrs), self.stack[-1] if self.stack else None)
        self.elements.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_endtag(self, tag):
        if not self.stack or self.stack[-1].tag != tag:
            raise ValueError(f"Unexpected closing tag {tag}")
        self.stack.pop()

    def first_legends(self):
        first = {}
        for element in self.elements:
            if element.tag == "legend" and element.parent.tag == "fieldset":
                first.setdefault(element.parent, element)
        return first

    def print_receipts(self):
        forms = {node.attrs["id"]: node for node in self.elements
                 if node.tag == "form" and "data-folio" in node.attrs}
        values = {key: [] for key in forms}
        legends = self.first_legends()
        options = {}
        for element in self.elements:
            if element.tag != "option" or "selected" not in element.attrs or "disabled" in element.attrs:
                continue
            for given in element.ancestors():
                if given.tag == "optgroup" and "disabled" in given.attrs:
                    break
                if given.tag == "select":
                    options.setdefault(given, []).append(element.attrs["value"])
                    break

        for control in self.elements:
            attrs = control.attrs
            if attrs.get("name") != "mark" or "disabled" in attrs:
                continue
            ancestors = tuple(control.ancestors())
            inherited = any(node.tag == "fieldset" and "disabled" in node.attrs
                            and legends.get(node) not in ancestors for node in ancestors)
            if inherited:
                continue
            owner = attrs.get("form")
            if owner is None:
                owner = next((node.attrs.get("id") for node in ancestors if node.tag == "form"), None)
            if owner not in values:
                continue

            if control.tag == "input":
                if attrs.get("type") not in ("checkbox", "radio") or "checked" in attrs:
                    values[owner].append(attrs["value"])
            elif control.tag == "select":
                values[owner].extend(options.get(control, ()))
            elif control.tag == "button" and attrs.get("data-edition") == "register":
                values[owner].append(attrs["value"])

        return [
            (form.attrs["data-folio"], form.attrs["data-impression"], tuple(values[key]))
            for key, form in forms.items()
        ]


def layout(receipts, marks):
    expected_folios = {f"{folio:02d}" for folio in range(1, 27)}
    counts = Counter(folio for folio, _, _ in receipts)
    if set(counts) != expected_folios or set(counts.values()) != {8}:
        raise ValueError("The four wards do not contain all 208 proofs")
    if len(marks) != 78 or len(set(marks)) != 78:
        raise ValueError("Expected 78 distinct registered marks")

    by_column = {key: set() for key in [*expected_folios, *marks]}
    constraints = []
    for index, (folio, _, values) in enumerate(receipts):
        if len(set(values)) != 3 or len(values) != 3 or any(mark not in marks for mark in values):
            raise ValueError(f"Incorrect native receipt for folio {folio}")
        row = (folio, *values)
        constraints.append(row)
        for column in row:
            by_column[column].add(index)

    def place(row):
        removed = []
        for column in constraints[row]:
            for conflict in by_column[column]:
                for peer in constraints[conflict]:
                    if peer != column:
                        by_column[peer].remove(conflict)
            removed.append(by_column.pop(column))
        return removed

    def undo(row, removed):
        for column, entries in reversed(list(zip(constraints[row], removed, strict=True))):
            by_column[column] = entries
            for other in entries:
                for peer in constraints[other]:
                    if peer != column:
                        by_column[peer].add(other)

    solutions = []

    def search(selected):
        if not by_column:
            solutions.append(tuple(selected))
            return
        key = min(by_column, key=lambda col: (len(by_column[col]), col))
        for row in sorted(by_column[key]):
            removed = place(row)
            selected.append(row)
            search(selected)
            selected.pop()
            undo(row, removed)
            if len(solutions) >= 2:
                return

    search([])
    if len(solutions) != 1:
        raise ValueError(f"The layout does not have one exact cover ({len(solutions)} found)")
    return sorted(receipts[index] for index in solutions[0])


def read_receipts(base, ticket):
    receipts = []
    for ward in ticket["wards"]:
        if not ward["url"].startswith(f'/press/{ticket["case"]}/'):
            raise ValueError("Ward link belongs to a different edition")
        with urlopen(base + ward["url"], timeout=15) as response:
            receipts.extend(Ward(response.read().decode("utf-8")).print_receipts())
    return receipts


def answer_for(receipts, marks):
    registry = "".join(" ".join((folio, impression, *values)) + "\n"
                       for folio, impression, values in layout(receipts, marks))
    return hashlib.sha256(registry.encode("ascii")).hexdigest()


def post(base, path, payload):
    request = Request(base + path, data=json.dumps(payload).encode(), method="POST",
                      headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=15) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("base_url", nargs="?", default="http://127.0.0.1:8003")
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    ticket = post(base, "/api/case", {})
    answer = answer_for(read_receipts(base, ticket), ticket["slots"])
    print(post(base, "/api/submit", {"case": ticket["case"], "answer": answer})["flag"])


if __name__ == "__main__":
    main()
