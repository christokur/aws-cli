"""Normalize changelog."""  # noqa: INP001

import contextlib
import pathlib

CHANGELOG = "CHANGELOG.md"

with contextlib.closing(pathlib.Path(CHANGELOG).open("r", encoding="utf-8")) as clf:
    lines = clf.readlines()

deduped = []
for line in lines:
    if not deduped or line != deduped[-1]:
        deduped.append(line)

with contextlib.closing(pathlib.Path(CHANGELOG).open("w", encoding="utf-8")) as clf:
    clf.writelines(deduped)
