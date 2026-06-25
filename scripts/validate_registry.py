#!/usr/bin/env python3
"""Validate the AI Qlik Sense Master Skill routing and catalog files."""

from __future__ import annotations

import sys

from qlik_master import doctor, emit


def main() -> int:
    result = doctor()
    emit(result)
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
