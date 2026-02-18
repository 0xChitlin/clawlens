"""
history.py — SQLite time-series storage for ClawLens metrics, sessions, and crons.
Provides HistoryDB (storage) and HistoryCollector (background collector thread).
"""

import json
import math
import os
import sqlite3
import threading
import time
from typing import Callable, Dict, List, Optional


# ---------------------------------------------------------------------------
# HistoryDB
# ---------------------------------------------------------------------------

class HistoryDB:
    """SQLite-backed storage for historical metrics, sessions, and cron data."""

    DEFAULT_DB_PATH = os.path.expanduser("~/.clawlens-history.db")

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or self.DEFAULT_DB_PATH
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
        )
        self._init_db()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _init_db(self):
        """Create tables, indexes, and set PRAGMAs."""
        c = self._conn.cursor()
        c.executescript("""
            PRAGMA journal_mode=WAL;
            PRAGMA auto_vacuum=INCREMENTAL;

            CREATE TABLE IF NOT EXISTS metrics (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                ts          REAL    NOT NULL,
                metric      TEXT    NOT NULL,
                value       REAL,
                value_text  TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_metrics_ts     ON metrics(ts);
            CREATE INDEX IF NOT EXISTS idx_metrics_metric ON metrics(metric);

            CREATE TABLE IF NOT EXISTS sessions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                ts          REAL    NOT NULL,
                session_key TEXT    NOT NULL,
                data        TEXT    NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_sessions_ts ON sessions(ts);

            CREATE TABLE IF NOT EXISTS crons (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                ts      REAL    NOT NULL,
                job_id  TEXT    NOT NULL,
                data    TEXT    NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_crons_ts ON crons(ts);
        """)
        self._conn.commit()

    def _execute(self, sql: str, params: tuple = ()):
        """Thread-safe write helper."""
        with self._lock:
            c = self._conn.cursor()
            c.execute(sql, params)
            self._conn.commit()
            return c

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------

    def record_metrics(self, ts: float, data: dict):
        """
        Store a metrics snapshot keyed by metric name.

        `data` can be:
          - {"cost_total": 1.23, "tokens_in_total": 500, ...}  — numeric metrics
          - a plain string key like "snapshot" with a JSON string value
            (detected when called as record_metrics("snapshot", json_str))

        To support the collector calling record_metrics(ts, dict) and also
        record_metrics("snapshot", json_str), we detect the calling pattern.
        """
        # Detect the alternate signature: record_metrics(metric_name_str, value_str)
        # This happens when the collector does record_metrics("snapshot", json.dumps(...))
        if isinstance(ts, str):
            metric_name = ts
            raw = data
            now = time.time()
            if isinstance(raw, (int, float)):
                self._execute(
                    "INSERT INTO metrics (ts, metric, value, value_text) VALUES (?, ?, ?, NULL)",
                    (now, metric_name, float(raw)),
                )
            else:
                self._execute(
                    "INSERT INTO metrics (ts, metric, value, value_text) VALUES (?, ?, NULL, ?)",
                    (now, metric_name, str(raw)),
                )
            return

        # Normal signature: record_metrics(ts: float, data: dict)
        with self._lock:
            c = self._conn.cursor()
            for metric, value in data.items():
                if isinstance(value, (int, float)):
                    c.execute(
                        "INSERT INTO metrics (ts, metric, value, value_text) VALUES (?, ?, ?, NULL)",
                        (ts, metric, float(value)),
                    )
                else:
                    c.execute(
                        "INSERT INTO metrics (ts, metric, value, value_text) VALUES (?, ?, NULL, ?)",
                        (ts, metric, str(value)),
                    )
            self._conn.commit()

    def query_metrics(
        self,
        metric: str,
        from_ts: float,
        to_ts: float,
        interval: int = 300,
    ) -> Dict:
        """
        Return time-bucketed average values for a metric.

        Buckets rows by floor(ts / interval) * interval and returns the
        average numeric value per bucket.

        Returns: {"points": [[bucket_ts, avg_val], ...]} sorted by ts.
        """
        c = self._conn.cursor()
        c.execute(
            """
            SELECT
                CAST(FLOOR(ts / ?) * ? AS REAL) AS bucket,
                AVG(value) AS avg_val
            FROM metrics
            WHERE metric = ?
              AND ts >= ?
              AND ts <= ?
              AND value IS NOT NULL
            GROUP BY bucket
            ORDER BY bucket ASC
            """,
            (interval, interval, metric, from_ts, to_ts),
        )
        rows = c.fetchall()
        points = [[row[0], row[1]] for row in rows if row[1] is not None]
        return {"points": points}

    def get_available_metrics(self) -> Dict:
        """Return distinct metric names stored in the DB."""
        c = self._conn.cursor()
        c.execute("SELECT DISTINCT metric FROM metrics ORDER BY metric ASC")
        rows = c.fetchall()
        return {"metrics": [r[0] for r in rows]}

    # ------------------------------------------------------------------
    # Sessions
    # ------------------------------------------------------------------

    def record_session(self, ts: float, session_key: str, data: dict):
        """Store a session snapshot."""
        self._execute(
            "INSERT INTO sessions (ts, session_key, data) VALUES (?, ?, ?)",
            (ts, session_key, json.dumps(data)),
        )

    def query_sessions(
        self,
        from_ts: float,
        to_ts: float,
        session_key: Optional[str] = None,
    ) -> Dict:
        """
        Return session history in the given time range.
        Optionally filter by session_key.
        """
        c = self._conn.cursor()
        if session_key:
            c.execute(
                """
                SELECT ts, session_key, data FROM sessions
                WHERE ts >= ? AND ts <= ? AND session_key = ?
                ORDER BY ts ASC
                """,
                (from_ts, to_ts, session_key),
            )
        else:
            c.execute(
                """
                SELECT ts, session_key, data FROM sessions
                WHERE ts >= ? AND ts <= ?
                ORDER BY ts ASC
                """,
                (from_ts, to_ts),
            )
        rows = c.fetchall()
        sessions = []
        for row in rows:
            try:
                d = json.loads(row[2])
            except (json.JSONDecodeError, TypeError):
                d = {"raw": row[2]}
            d["_ts"] = row[0]
            d["_session_key"] = row[1]
            sessions.append(d)
        return {"sessions": sessions}

    # ------------------------------------------------------------------
    # Crons
    # ------------------------------------------------------------------

    def record_cron(self, ts: float, job_id: str, data: dict):
        """Store a cron run record."""
        self._execute(
            "INSERT INTO crons (ts, job_id, data) VALUES (?, ?, ?)",
            (ts, job_id, json.dumps(data)),
        )

    def query_crons(
        self,
        from_ts: float,
        to_ts: float,
        job_id: Optional[str] = None,
    ) -> Dict:
        """
        Return cron history in the given time range.
        Optionally filter by job_id.
        """
        c = self._conn.cursor()
        if job_id:
            c.execute(
                """
                SELECT ts, job_id, data FROM crons
                WHERE ts >= ? AND ts <= ? AND job_id = ?
                ORDER BY ts ASC
                """,
                (from_ts, to_ts, job_id),
            )
        else:
            c.execute(
                """
                SELECT ts, job_id, data FROM crons
                WHERE ts >= ? AND ts <= ?
                ORDER BY ts ASC
                """,
                (from_ts, to_ts),
            )
        rows = c.fetchall()
        crons = []
        for row in rows:
            try:
                d = json.loads(row[2])
            except (json.JSONDecodeError, TypeError):
                d = {"raw": row[2]}
            d["_ts"] = row[0]
            d["_job_id"] = row[1]
            crons.append(d)
        return {"crons": crons}

    # ------------------------------------------------------------------
    # Snapshots
    # ------------------------------------------------------------------

    def query_snapshot(self, timestamp: float) -> Dict:
        """
        Find the snapshot row in metrics closest to the given timestamp.
        Parses value_text as JSON and returns it.
        """
        c = self._conn.cursor()
        c.execute(
            """
            SELECT value_text FROM metrics
            WHERE metric = 'snapshot' AND value_text IS NOT NULL
            ORDER BY ABS(ts - ?) ASC
            LIMIT 1
            """,
            (timestamp,),
        )
        row = c.fetchone()
        if not row:
            return {"snapshot": {}}
        try:
            snapshot = json.loads(row[0])
        except (json.JSONDecodeError, TypeError):
            snapshot = {"raw": row[0]}
        return {"snapshot": snapshot}

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_stats(self) -> Dict:
        """Return overall DB statistics."""
        c = self._conn.cursor()
        c.execute("SELECT COUNT(*), MIN(ts), MAX(ts) FROM metrics")
        row = c.fetchone()
        total_points = row[0] or 0
        oldest_ts = row[1] or 0.0
        newest_ts = row[2] or 0.0

        try:
            db_size_bytes = os.path.getsize(self.db_path)
        except OSError:
            db_size_bytes = 0

        return {
            "total_points": total_points,
            "oldest_ts": oldest_ts,
            "newest_ts": newest_ts,
            "db_size_bytes": db_size_bytes,
        }

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self):
        """Close the database connection."""
        try:
            self._conn.close()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# HistoryCollector
# ---------------------------------------------------------------------------

class HistoryCollector:
    """
    Background daemon thread that periodically collects metrics from the
    OpenClaw gateway and stores them in HistoryDB.

    Collects every 60 seconds:
      - session_status  → cost_total, tokens_in_total, tokens_out_total
      - sessions_list   → sessions_active count
      - cron list       → cron states
      - full snapshot   → all collected data as JSON in metrics("snapshot")
    """

    INTERVAL = 60  # seconds between collections

    def __init__(self, db: HistoryDB, gw_invoke: Callable):
        self._db = db
        self._gw_invoke = gw_invoke
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self):
        """Start the background collector thread (daemon)."""
        if self._thread and self._thread.is_alive():
            return  # already running
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            name="HistoryCollector",
            daemon=True,
        )
        self._thread.start()

    def stop(self):
        """Signal the collector thread to stop."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)

    # ------------------------------------------------------------------
    # Collection loop
    # ------------------------------------------------------------------

    def _run(self):
        """Main loop: collect immediately, then every INTERVAL seconds."""
        while not self._stop_event.is_set():
            try:
                self._collect()
            except Exception:
                pass  # never crash the thread
            # Sleep in short increments so stop() is responsive
            for _ in range(self.INTERVAL * 10):
                if self._stop_event.is_set():
                    return
                time.sleep(0.1)

    def _collect(self):
        """Perform one collection cycle."""
        now = time.time()
        all_data: Dict = {}

        # --- session_status ---
        try:
            status = self._gw_invoke("session_status", {})
            if isinstance(status, dict):
                cost = self._safe_float(status.get("cost_total"))
                tok_in = self._safe_float(status.get("tokens_in_total"))
                tok_out = self._safe_float(status.get("tokens_out_total"))

                metrics_data: Dict = {}
                if cost is not None:
                    metrics_data["cost_total"] = cost
                if tok_in is not None:
                    metrics_data["tokens_in_total"] = tok_in
                if tok_out is not None:
                    metrics_data["tokens_out_total"] = tok_out

                if metrics_data:
                    self._db.record_metrics(now, metrics_data)

                all_data["session_status"] = status
        except Exception:
            pass

        # --- sessions_list → sessions_active count ---
        try:
            sessions_resp = self._gw_invoke(
                "sessions_list", {"limit": 50, "messageLimit": 0}
            )
            if isinstance(sessions_resp, dict):
                sessions = sessions_resp.get("sessions", [])
                if isinstance(sessions, list):
                    active_count = len(sessions)
                    self._db.record_metrics(now, {"sessions_active": float(active_count)})
                    all_data["sessions_list"] = sessions_resp
        except Exception:
            pass

        # --- cron list ---
        try:
            cron_resp = self._gw_invoke("cron", {"action": "list"})
            if isinstance(cron_resp, dict):
                jobs = cron_resp.get("jobs", cron_resp.get("crons", []))
                if isinstance(jobs, list):
                    for job in jobs:
                        if not isinstance(job, dict):
                            continue
                        job_id = job.get("id") or job.get("name") or "unknown"
                        # Record cron if it has a recent lastRun
                        last_run = job.get("lastRun") or job.get("last_run")
                        if last_run:
                            try:
                                last_ts = float(last_run) / 1000 if float(last_run) > 1e10 else float(last_run)
                            except (TypeError, ValueError):
                                last_ts = now
                            self._db.record_cron(last_ts, str(job_id), job)
                all_data["cron"] = cron_resp
        except Exception:
            pass

        # --- full snapshot ---
        try:
            snapshot_json = json.dumps(all_data)
            self._db._execute(
                "INSERT INTO metrics (ts, metric, value, value_text) VALUES (?, 'snapshot', NULL, ?)",
                (now, snapshot_json),
            )
        except Exception:
            pass

    @staticmethod
    def _safe_float(val) -> Optional[float]:
        """Safely convert a value to float, returning None on failure."""
        if val is None:
            return None
        try:
            return float(val)
        except (TypeError, ValueError):
            return None
