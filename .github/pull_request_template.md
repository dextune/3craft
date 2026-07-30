# Pull request

## Summary

<!-- Explain what changed and why. -->

## Related issue

<!-- Example: Closes #123 -->

## Validation

- [ ] `.venv/bin/python -m pytest -q`
- [ ] `npm --prefix apps/web run build`
- [ ] Targeted smoke test or independent parser validation required by this change

Commands and results:

```text

```

## Contract and risk review

- [ ] Preserves provenance and evidence-class invariants.
- [ ] Preserves image-first precedence and fail-closed handling of invalid supplied images.
- [ ] Preserves fail-closed delivery and private-artifact policies.
- [ ] Contains no user content, secrets, or local runtime artifacts.
- [ ] Reviews version, license, data egress, and cost for any new dependency or provider.
- [ ] Verifies cleanup when adding Three.js resources or asynchronous polling.

## Documentation and compatibility

- [ ] Updates documentation for any changed user behavior or public contract.
- [ ] Describes effects on Java 1.20.4/DataVersion 3700/Sponge v3 compatibility.
- [ ] Records known limitations and follow-up work.

## Screenshots or artifact information

<!-- Include only when needed, and remove private images and runtime artifacts. -->
