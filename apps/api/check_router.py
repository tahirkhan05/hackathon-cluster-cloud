#!/usr/bin/env python
"""Check if tasks router loads properly."""

try:
    from domains.tasks.router import router
    print(f"✓ Router loaded: {router}")
    print(f"✓ Total routes: {len(router.routes)}")
    for r in router.routes:
        print(f"  - {r.path}")
except Exception as e:
    print(f"✗ Error loading router: {e}")
    import traceback
    traceback.print_exc()
