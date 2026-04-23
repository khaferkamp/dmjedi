# Release Checklist

Use this checklist before creating the final `v0.2.0` tag and GitHub release.

## 1. Refresh generated artifacts if needed

- Re-run the commands in `examples/generated/README.md`
- Confirm `examples/generated/duckdb`, `examples/generated/databricks`, `examples/generated/postgres`, `examples/generated/spark-batch`, and `examples/generated/spark-streaming` all exist and contain files

## 2. Run validation commands

```bash
uv run pytest --no-cov tests/test_cli.py tests/test_mcp.py tests/test_generators.py tests/test_integration.py -k "mode or streaming" -x
uv run pytest --no-cov tests/test_integration.py -k "example or generated" -x
uv run pytest
```

## 3. Review release docs

- Confirm `CHANGELOG.md` contains the final `## v0.2.0` release notes
- Confirm `README.md` install instructions still match `uv pip install -e ".[dev]"`
- Confirm `README.md` points to `examples/generated/` and this checklist

## 4. Prepare the tag

```bash
git status
git tag v0.2.0
```

- If the working tree is not clean, stop and resolve that before tagging

## 5. Publish the GitHub release

- This step is manual
- Create the GitHub release for tag `v0.2.0`
- Paste the `CHANGELOG.md` `## v0.2.0` section into the release notes body
- Include install instructions and a pointer to `examples/generated/`

## 6. Post-publish spot check

- Confirm the GitHub release page shows the correct tag and notes
- Confirm the repo still passes `uv run pytest` after the release commit/tag state
