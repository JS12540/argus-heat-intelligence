# FortyGuard API exploration scripts

One-off manual scripts that hit the **live** FortyGuard API to confirm real endpoint paths,
payload shapes, and response shapes. These are NOT a test suite (there isn't one, by design —
see repo history) and are not run in CI. Run each individually, once, when you need to verify
something against the real API:

```bash
cd backend
.venv/bin/python scripts/test_create_heatmap.py
```

Every script uses a small AOI / minimal granularity (60m) to keep credit cost down, and a fixed
historical test date (`2025-07-15`) already confirmed to have real data. Endpoints whose exact
submission path isn't documented (Heat Intelligence, Environmental Parameters, Satellite/Street
View Segmentation) probe a short list of candidate paths first and report which one the API
actually accepts, rather than guessing blind.

**These cost real FortyGuard credits on `Completed` activities.** Don't loop these in CI or run
them repeatedly — they exist to answer "what does this endpoint actually do," once.
