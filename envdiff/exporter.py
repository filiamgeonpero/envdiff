"""Export comparison results to JSON or CSV formats."""
import csv
import json
import io
from typing import Literal
from envdiff.comparator import CompareResult

Format = Literal["json", "csv"]


def export_result(result: CompareResult, fmt: Format) -> str:
    """Serialize a CompareResult to the requested format string."""
    if fmt == "json":
        return _to_json(result)
    if fmt == "csv":
        return _to_csv(result)
    raise ValueError(f"Unsupported format: {fmt}")


def _to_json(result: CompareResult) -> str:
    data = {
        "envs": result.env_names,
        "diffs": [
            {
                "key": d.key,
                "missing_in": d.missing_in,
                "values": d.values,
            }
            for d in result.diffs
        ],
    }
    return json.dumps(data, indent=2)


def _to_csv(result: CompareResult) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["key", "type", "detail"])
    for d in result.diffs:
        if d.missing_in:
            writer.writerow([d.key, "missing", ",".join(d.missing_in)])
        elif d.values:
            detail = " | ".join(f"{e}={v}" for e, v in d.values.items())
            writer.writerow([d.key, "mismatch", detail])
    return buf.getvalue()
