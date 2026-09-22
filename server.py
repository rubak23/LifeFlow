"""LifeFlow local application server with a persistent SQLite database."""

from __future__ import annotations

import json
import mimetypes
import sqlite3
from datetime import datetime
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent
WEB_ROOT = ROOT / "dist"
DEFAULT_DB = ROOT / "data" / "lifeflow.db"
mimetypes.add_type("application/javascript", ".js")


class ClosingConnection(sqlite3.Connection):
    """Commit/rollback and release the Windows file handle after every operation."""

    def __exit__(self, exc_type, exc_value, traceback):
        result = super().__exit__(exc_type, exc_value, traceback)
        self.close()
        return result


class LifeFlowDatabase:
    def __init__(self, path: Path | str = DEFAULT_DB):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self):
        connection = sqlite3.connect(self.path, factory=ClosingConnection)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self):
        with self.connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS blood_units (
                    id TEXT PRIMARY KEY, blood_type TEXT NOT NULL, component TEXT NOT NULL,
                    branch TEXT NOT NULL, expires TEXT NOT NULL, status TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS blood_requests (
                    id TEXT PRIMARY KEY, patient_code TEXT NOT NULL, hospital TEXT NOT NULL,
                    blood_type TEXT NOT NULL, units INTEGER NOT NULL, urgency TEXT NOT NULL,
                    status TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS donations (
                    id TEXT PRIMARY KEY, donor_name TEXT NOT NULL, blood_type TEXT NOT NULL,
                    donation_date TEXT NOT NULL, status TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, event_time TEXT NOT NULL,
                    user_name TEXT NOT NULL, action TEXT NOT NULL, record_id TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS donors (
                    id TEXT PRIMARY KEY, full_name TEXT NOT NULL, phone TEXT NOT NULL,
                    blood_type TEXT NOT NULL, conditions TEXT NOT NULL,
                    last_donation TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS screenings (
                    id TEXT PRIMARY KEY, donation_id TEXT NOT NULL, unit_id TEXT NOT NULL,
                    hiv TEXT NOT NULL, hbv TEXT NOT NULL, hcv TEXT NOT NULL,
                    syphilis TEXT NOT NULL, result TEXT NOT NULL, tested_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS lab_orders (
                    id TEXT PRIMARY KEY, patient_name TEXT NOT NULL, patient_code TEXT NOT NULL,
                    symptoms TEXT NOT NULL, test_type TEXT NOT NULL, doctor TEXT NOT NULL,
                    status TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_units_status ON blood_units(status);
                CREATE INDEX IF NOT EXISTS idx_screenings_result ON screenings(result);
                CREATE INDEX IF NOT EXISTS idx_lab_orders_status ON lab_orders(status);
                """
            )
            if db.execute("SELECT COUNT(*) FROM blood_units").fetchone()[0] == 0:
                db.executemany(
                    "INSERT INTO blood_units VALUES (?,?,?,?,?,?)",
                    [
                        ("LF-2048", "O+", "Red cells", "Soroka", "2026-10-20", "Available"),
                        ("LF-2049", "O-", "Red cells", "Soroka", "2026-10-03", "Available"),
                        ("LF-2050", "A+", "Plasma", "Barzilai", "2027-09-11", "Available"),
                        ("LF-2051", "A-", "Red cells", "Soroka", "2026-10-12", "Reserved"),
                        ("LF-2052", "B+", "Platelets", "Assuta Ashdod", "2026-09-23", "Pending Testing"),
                        ("LF-2053", "AB-", "Red cells", "Soroka", "2026-10-06", "Available"),
                        ("LF-2054", "B-", "Red cells", "Barzilai", "2026-10-09", "Available"),
                        ("LF-2055", "AB+", "Plasma", "Soroka", "2027-09-16", "Available"),
                    ],
                )
            if db.execute("SELECT COUNT(*) FROM blood_requests").fetchone()[0] == 0:
                now = datetime.now().isoformat(timespec="seconds")
                db.executemany(
                    "INSERT INTO blood_requests VALUES (?,?,?,?,?,?,?,?)",
                    [("REQ-1042", "PT-88320", "Soroka", "A+", 2, "Critical", "Matched", now),
                     ("REQ-1043", "PT-88341", "Barzilai", "O-", 1, "Urgent", "Open", now),
                     ("REQ-1044", "PT-88376", "Assuta Ashdod", "B+", 2, "Routine", "Open", now)],
                )
            if db.execute("SELECT COUNT(*) FROM donations").fetchone()[0] == 0:
                db.executemany(
                    "INSERT INTO donations VALUES (?,?,?,?,?)",
                    [("DON-3108", "Dana Levy", "O+", "2026-09-20", "Approved"),
                     ("DON-3109", "Amir Halevi", "A-", "2026-09-20", "Testing"),
                     ("DON-3110", "Maya Cohen", "B+", "2026-09-19", "Approved")],
                )
            if db.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0] == 0:
                db.executemany(
                    "INSERT INTO audit_log(event_time,user_name,action,record_id) VALUES (?,?,?,?)",
                    [("09:42", "Maya Cohen", "Approved unit", "LF-2048"),
                     ("09:27", "Noa Adler", "Matched critical request", "REQ-1042"),
                     ("08:51", "System", "Raised low-stock alert", "O-")],
                )
            if db.execute("SELECT COUNT(*) FROM donors").fetchone()[0] == 0:
                db.executemany(
                    "INSERT INTO donors VALUES (?,?,?,?,?,?)",
                    [("DNR-1001", "Dana Levy", "050-1234567", "O+", "None reported", "2026-09-20"),
                     ("DNR-1002", "Amir Halevi", "052-7654321", "A-", "Seasonal allergy", "2026-09-20"),
                     ("DNR-1003", "Maya Cohen", "054-2468101", "B+", "None reported", "2026-09-19")],
                )
            if db.execute("SELECT COUNT(*) FROM screenings").fetchone()[0] == 0:
                db.executemany(
                    "INSERT INTO screenings VALUES (?,?,?,?,?,?,?,?,?)",
                    [("SCR-5001", "DON-3108", "LF-2048", "Negative", "Negative", "Negative", "Negative", "Clean", "2026-09-20 09:40"),
                     ("SCR-5002", "DON-3109", "LF-2052", "Pending", "Pending", "Pending", "Pending", "Pending", "")],
                )
            if db.execute("SELECT COUNT(*) FROM lab_orders").fetchone()[0] == 0:
                db.executemany(
                    "INSERT INTO lab_orders VALUES (?,?,?,?,?,?,?,?)",
                    [("LAB-7001", "Yael Cohen", "PT-77120", "Fatigue and dizziness", "CBC + Ferritin", "Dr. Haddad", "Results ready", "2026-09-20T08:20:00"),
                     ("LAB-7002", "Omar Ali", "PT-77121", "Persistent thirst", "Glucose + HbA1c", "Dr. Levi", "In laboratory", "2026-09-20T09:10:00")],
                )
            db.execute("PRAGMA optimize")

    @staticmethod
    def rows(cursor):
        return [dict(row) for row in cursor.fetchall()]

    def state(self):
        with self.connect() as db:
            inventory = self.rows(db.execute("SELECT id,blood_type AS type,component,branch,expires,status FROM blood_units ORDER BY id"))
            requests = self.rows(db.execute("SELECT id,patient_code AS patient,hospital,blood_type AS type,units,urgency,status FROM blood_requests ORDER BY created_at DESC"))
            donations = self.rows(db.execute("SELECT id,donor_name AS donor,blood_type AS type,donation_date AS date,status FROM donations ORDER BY donation_date DESC,id DESC"))
            audit = self.rows(db.execute("SELECT event_time AS time,user_name AS user,action,record_id AS record FROM audit_log ORDER BY id DESC LIMIT 50"))
            donors = self.rows(db.execute("SELECT id,full_name AS name,phone,blood_type AS type,conditions,last_donation AS lastDonation FROM donors ORDER BY full_name"))
            screenings = self.rows(db.execute("SELECT id,donation_id AS donationId,unit_id AS unitId,hiv,hbv,hcv,syphilis,result,tested_at AS testedAt FROM screenings ORDER BY id DESC"))
            lab_orders = self.rows(db.execute("SELECT id,patient_name AS patient,patient_code AS patientCode,symptoms,test_type AS testType,doctor,status FROM lab_orders ORDER BY created_at DESC"))
        return {"inventory": inventory, "requests": requests, "donations": donations, "audit": audit, "donors": donors, "screenings": screenings, "labOrders": lab_orders}

    def add_request(self, item):
        with self.connect() as db:
            next_id = f"REQ-{1042 + db.execute('SELECT COUNT(*) FROM blood_requests').fetchone()[0]}"
            db.execute("INSERT INTO blood_requests VALUES (?,?,?,?,?,?,?,?)", (next_id, item["patient"], item["hospital"], item["type"], int(item["units"]), item["urgency"], "Open", datetime.now().isoformat(timespec="seconds")))
            self._audit(db, item.get("user", "Noa Adler"), "Created request", next_id)
        return next_id

    def add_donation(self, item):
        with self.connect() as db:
            next_id = f"DON-{3108 + db.execute('SELECT COUNT(*) FROM donations').fetchone()[0]}"
            next_unit = f"LF-{2048 + db.execute('SELECT COUNT(*) FROM blood_units').fetchone()[0]}"
            next_donor = f"DNR-{1001 + db.execute('SELECT COUNT(*) FROM donors').fetchone()[0]}"
            next_screening = f"SCR-{5001 + db.execute('SELECT COUNT(*) FROM screenings').fetchone()[0]}"
            db.execute("INSERT INTO donations VALUES (?,?,?,?,?)", (next_id, item["donor"], item["type"], datetime.now().date().isoformat(), "Testing"))
            existing = db.execute("SELECT id FROM donors WHERE full_name=?", (item["donor"],)).fetchone()
            if existing:
                db.execute("UPDATE donors SET phone=?,blood_type=?,conditions=?,last_donation=? WHERE id=?", (item.get("phone", "Not provided"), item["type"], item.get("conditions", "None reported"), datetime.now().date().isoformat(), existing["id"]))
            else:
                db.execute("INSERT INTO donors VALUES (?,?,?,?,?,?)", (next_donor, item["donor"], item.get("phone", "Not provided"), item["type"], item.get("conditions", "None reported"), datetime.now().date().isoformat()))
            db.execute("INSERT INTO blood_units VALUES (?,?,?,?,?,?)", (next_unit, item["type"], "Red cells", item.get("branch", "Soroka"), item.get("expires", "2026-11-01"), "Pending Testing"))
            db.execute("INSERT INTO screenings VALUES (?,?,?,?,?,?,?,?,?)", (next_screening, next_id, next_unit, "Pending", "Pending", "Pending", "Pending", "Pending", ""))
            self._audit(db, item.get("user", "Noa Adler"), "Registered donation", next_id)
        return {"donation_id": next_id, "unit_id": next_unit}

    def complete_screening(self, item):
        tests = [item.get(name, "Negative") for name in ("hiv", "hbv", "hcv", "syphilis")]
        result = "Clean" if all(value == "Negative" for value in tests) else "Rejected"
        with self.connect() as db:
            row = db.execute("SELECT donation_id,unit_id FROM screenings WHERE id=?", (item["screening_id"],)).fetchone()
            if not row:
                raise ValueError("Screening not found")
            db.execute("UPDATE screenings SET hiv=?,hbv=?,hcv=?,syphilis=?,result=?,tested_at=? WHERE id=?", (*tests, result, datetime.now().strftime("%Y-%m-%d %H:%M"), item["screening_id"]))
            db.execute("UPDATE donations SET status=? WHERE id=?", ("Approved" if result == "Clean" else "Rejected", row["donation_id"]))
            db.execute("UPDATE blood_units SET status=? WHERE id=?", ("Available" if result == "Clean" else "Rejected", row["unit_id"]))
            self._audit(db, item.get("user", "Noa Adler"), f"Screening {result}", row["unit_id"])
        return result

    def add_lab_order(self, item):
        with self.connect() as db:
            next_id = f"LAB-{7001 + db.execute('SELECT COUNT(*) FROM lab_orders').fetchone()[0]}"
            db.execute("INSERT INTO lab_orders VALUES (?,?,?,?,?,?,?,?)", (next_id, item["patient"], item["patientCode"], item["symptoms"], item["testType"], item["doctor"], "Ordered", datetime.now().isoformat(timespec="seconds")))
            self._audit(db, item.get("user", "Dr. Haddad"), "Ordered patient blood test", next_id)
        return next_id

    def reserve(self, unit_id, request_id, user="Noa Adler"):
        with self.connect() as db:
            changed = db.execute("UPDATE blood_units SET status='Reserved' WHERE id=? AND status='Available'", (unit_id,)).rowcount
            if not changed:
                return False
            db.execute("UPDATE blood_requests SET status='Matched' WHERE id=?", (request_id,))
            self._audit(db, user, "Reserved compatible unit", unit_id)
        return True

    @staticmethod
    def _audit(db, user, action, record):
        db.execute("INSERT INTO audit_log(event_time,user_name,action,record_id) VALUES (?,?,?,?)", (datetime.now().strftime("%H:%M"), user, action, record))


class LifeFlowHandler(SimpleHTTPRequestHandler):
    database = LifeFlowDatabase()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_ROOT), **kwargs)

    def send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if urlparse(self.path).path == "/api/state":
            return self.send_json(self.database.state())
        if urlparse(self.path).path == "/api/health":
            return self.send_json({"status": "ok", "database": "sqlite"})
        return super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            length = int(self.headers.get("Content-Length", "0"))
            data = json.loads(self.rfile.read(length) or b"{}")
            if path == "/api/requests":
                return self.send_json({"id": self.database.add_request(data)}, 201)
            if path == "/api/donations":
                return self.send_json(self.database.add_donation(data), 201)
            if path == "/api/screenings":
                return self.send_json({"result": self.database.complete_screening(data)})
            if path == "/api/lab-orders":
                return self.send_json({"id": self.database.add_lab_order(data)}, 201)
            if path == "/api/reservations":
                ok = self.database.reserve(data["unit_id"], data["request_id"], data.get("user", "Noa Adler"))
                return self.send_json({"reserved": ok}, 200 if ok else 409)
            return self.send_json({"error": "Unknown API endpoint"}, 404)
        except (KeyError, ValueError, json.JSONDecodeError) as error:
            return self.send_json({"error": str(error)}, 400)


def run(port=4173):
    server = ThreadingHTTPServer(("127.0.0.1", port), LifeFlowHandler)
    print(f"LifeFlow is running at http://localhost:{port}")
    print(f"SQLite database: {DEFAULT_DB}")
    server.serve_forever()
