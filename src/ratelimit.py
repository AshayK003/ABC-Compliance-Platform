# Shared slowapi rate-limiter instance.
#
# All route modules MUST import this instead of constructing their own
# Limiter: per-instance in-memory storage fragments accounting and makes
# limits impossible to reason about. The app wires this exact object as
# app.state.limiter in src/main.py.

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
