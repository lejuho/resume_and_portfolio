# Codex Review v2

## Verdict

PASS

Cycle 8 remains pass. This review adds a non-blocking hardening recommendation for output path parsing before the dashboard grows more build flows.

## Non-Blocking Recommendation

### Harden `_parse_output_path()` before paths get more varied

Current implementation:

- Uses `_OUTPUT_PATH_RE = re.compile(r"output[/\\](resumes|portfolios)[/\\]\S+\.(pdf|pptx)")`.
- Works for current generated paths and was verified against real Windows stdout:
  - `output\resumes\resume-20260520-1703.pdf`
  - `output\portfolios\portfolio-20260520-1703.pptx`

Potential future issue:

- `\S+` will stop at spaces.
- If a future output path, project folder, or custom `--out` path contains spaces, dashboard may fail to highlight the generated file even though the build succeeded.
- Wrapped stdout lines can also make regex-only extraction brittle.

Recommended short-term fix:

- Make `_parse_output_path()` line-based first, then keep regex as fallback.
- Accept:
  - relative paths under `output/resumes/` and `output/portfolios/`
  - Windows separators
  - absolute paths containing `\output\resumes\...` or `\output\portfolios\...`
  - paths with spaces as long as the line ends in `.pdf` or `.pptx`

Example direction:

```python
def _parse_output_path(stdout: str) -> str | None:
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    for line in lines:
        lowered = line.lower()
        if "output" in lowered and lowered.endswith((".pdf", ".pptx")):
            # Handles "Resume written: C:\\...\\output\\resumes\\file.pdf"
            return line.split(":", 1)[-1].strip() if ": " in line else line
    m = _OUTPUT_PATH_RE.search(stdout.replace("\r\n", "\n").replace("\r", "\n"))
    return m.group(0) if m else None
```

Add tests for:

- `Resume written: C:\some dir\output\resumes\resume with space.pdf`
- `Portfolio written:` on one line and the path on the next line
- relative `output/portfolios/my deck.pptx`
- dry-run stdout still returns `None`

Longer-term direction:

- Add a `--json` option to `pcli build resume/portfolio`.
- Dashboard should eventually consume structured JSON instead of parsing human stdout.
- That is larger than Cycle 8 polish and can be deferred.

## Checks Reconfirmed From v1

- `uv run pytest -v`: PASS, 148 tests
- `uv run ruff check scripts tests templates`: PASS
- `uv run ruff format --check scripts tests templates`: PASS
- `uv run pcli validate`: PASS
- Real dashboard build API returned `output_path` for both resume and portfolio builds.
