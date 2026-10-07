"""Vercel Python Function entry point for the hosted UAT console."""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from resilience.m22_web import ConsoleApplication, make_handler  # noqa: E402


handler = make_handler(ConsoleApplication())
