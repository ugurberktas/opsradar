# Contributing

Thanks for improving OpsRadar.

1. Create a focused branch.
2. Install backend and frontend dependencies using the README instructions.
3. Keep changes scoped and add regression tests for behavior changes.
4. Run `make lint test build audit`.
5. Explain user-visible behavior, security implications, and verification in
   the pull request.

Use synthetic logs and fictional service names in tests and examples. Never
commit credentials, local databases, generated builds, or operational data.

No code-format-only refactor should be mixed with a functional change unless it
is required for that change.
