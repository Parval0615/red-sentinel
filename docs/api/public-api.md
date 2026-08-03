# Public API Documentation Policy

RedSentinel documents a deliberately small stable research API. The executable
allowlist is [`public-api.json`](public-api.json); contract tests import every
listed symbol and require a non-empty docstring.

The allowlist covers:

- versioned research contracts;
- experiment, co-evolution, analysis, and provenance entry points;
- application services used by the optional API;
- profiling, attack-data, adapter, reporting, migration, and CLI entry points.

Constants, `Literal` aliases, implementation helpers, optional backend classes,
and legacy compatibility re-exports are excluded. Exclusion means they are not
stability promises; it does not mean they may bypass normal code review.

Run the gate with:

```bash
python -m pytest -q tests/contract/test_public_api_documentation.py
```

When adding a stable public class or function, add it to the allowlist and write
a docstring that states its input/output role, determinism, and material side
effects. Do not add narrative docstrings to trivial aliases merely to increase a
coverage percentage.
