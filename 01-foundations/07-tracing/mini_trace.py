import json
import time
import uuid
from pathlib import Path


class Trace:
    def __init__(self, run_name: str, out_dir: str = "traces"):
        self.run_id = str(uuid.uuid4())[:8]
        self.run_name = run_name
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.t0 = time.time()
        self.spans = []
        self.meta = {
            "run_id": self.run_id,
            "run_name": run_name,
            "started_at": time.time(),
        }

    def span(self, kind: str, **fields):
        item = {"kind": kind, "ts": time.time(), **fields}
        self.spans.append(item)
        if kind == "llm":
            print(
                f"[trace {self.run_id}] llm step={fields.get('step')} "
                f"latency_ms={fields.get('latency_ms')} "
                f"has_tools={fields.get('has_tool_calls')} "
                f"msgs={fields.get('messages_len')}"
            )
        elif kind == "tool":
            print(
                f"[trace {self.run_id}] tool step={fields.get('step')} "
                f"name={fields.get('name')} latency_ms={fields.get('latency_ms')}"
            )
        elif kind == "decision":
            print(
                f"[trace {self.run_id}] stop={fields.get('stop_reason')} "
                f"steps={fields.get('steps')}"
            )
        return item

    def finish(self, stop_reason: str, final: str, steps: int):
        self.meta.update(
            {
                "stop_reason": stop_reason,
                "steps": steps,
                "final": final,
                "duration_ms": int((time.time() - self.t0) * 1000),
                "ended_at": time.time(),
            }
        )
        self.span("decision", stop_reason=stop_reason, steps=steps)
        path = self.out_dir / f"{self.run_name}_{self.run_id}.json"
        payload = {"meta": self.meta, "spans": self.spans}
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[trace {self.run_id}] wrote {path}")
        return path
