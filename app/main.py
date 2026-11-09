"""InfraPilot's HTTP API."""

import os

import pymysql
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import PlainTextResponse

from app.diagnostics import check_tcp, host_snapshot
from app.storage import recent_snapshots, save_snapshot

app = FastAPI(
    title="InfraPilot",
    version="2.0.0",
    description="Local infrastructure diagnostics learning demo",
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "infrapilot", "version": app.version}


@app.get("/diagnostics")
def diagnostics():
    snapshot = host_snapshot()
    return save_snapshot(snapshot)


@app.get("/network-check")
def network_check(host: str = Query(min_length=1, max_length=253),
                  port: int = Query(ge=1, le=65535)):
    return check_tcp(host, port)


@app.get("/history")
def history(limit: int = Query(default=20, ge=1, le=100)):
    return {"items": recent_snapshots(limit)}


@app.get("/database-check")
def database_check():
    connection = None
    try:
        connection = pymysql.connect(
            host=os.getenv("MYSQL_HOST", "mysql"),
            port=int(os.getenv("MYSQL_PORT", "3306")),
            user=os.getenv("MYSQL_USER", "infrauser"),
            password=os.getenv("MYSQL_PASSWORD", ""),
            database=os.getenv("MYSQL_DATABASE", "infrapilot"),
            connect_timeout=3,
            read_timeout=3,
        )
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION(), DATABASE()")
            version, database = cursor.fetchone()
        return {
            "status": "ok",
            "database": database,
            "mysql_version": version,
        }
    except pymysql.MySQLError as exc:
        raise HTTPException(
            status_code=503,
            detail="MySQL connection failed",
        ) from exc
    finally:
        if connection is not None:
            connection.close()


@app.get("/metrics", include_in_schema=False, response_class=PlainTextResponse)
def metrics():
    snapshot = host_snapshot()
    lines = [
        "# HELP infrapilot_cpu_percent Host CPU use percent",
        "# TYPE infrapilot_cpu_percent gauge",
        f"infrapilot_cpu_percent {snapshot['cpu_percent']}",
        "# HELP infrapilot_memory_percent Host memory use percent",
        "# TYPE infrapilot_memory_percent gauge",
        f"infrapilot_memory_percent {snapshot['memory_percent']}",
        "# HELP infrapilot_disk_percent Host disk use percent",
        "# TYPE infrapilot_disk_percent gauge",
        f"infrapilot_disk_percent {snapshot['disk_percent']}",
    ]
    return "\n".join(lines) + "\n"