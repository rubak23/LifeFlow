import tempfile
import unittest
from pathlib import Path

from server import LifeFlowDatabase


class LifeFlowDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = LifeFlowDatabase(Path(self.temp.name) / "test.db")

    def tearDown(self):
        self.temp.cleanup()

    def test_seed_state_is_available(self):
        state = self.db.state()
        self.assertGreaterEqual(len(state["inventory"]), 8)
        self.assertGreaterEqual(len(state["requests"]), 3)

    def test_request_is_persisted_and_audited(self):
        request_id = self.db.add_request({"patient": "PT-TEST", "hospital": "Soroka", "type": "O-", "units": 2, "urgency": "Critical"})
        state = self.db.state()
        self.assertTrue(any(row["id"] == request_id for row in state["requests"]))
        self.assertTrue(any(row["record"] == request_id for row in state["audit"]))

    def test_donation_is_persisted(self):
        created = self.db.add_donation({"donor": "Test Donor", "phone": "050", "type": "A+", "conditions": "None"})
        state = self.db.state()
        self.assertTrue(any(row["id"] == created["donation_id"] for row in state["donations"]))
        self.assertTrue(any(row["id"] == created["unit_id"] and row["status"] == "Pending Testing" for row in state["inventory"]))
        self.assertTrue(any(row["name"] == "Test Donor" for row in state["donors"]))

    def test_clean_screening_releases_unit(self):
        created = self.db.add_donation({"donor": "Safe Donor", "type": "B+"})
        screening = next(row for row in self.db.state()["screenings"] if row["unitId"] == created["unit_id"])
        result = self.db.complete_screening({"screening_id": screening["id"], "hiv": "Negative", "hbv": "Negative", "hcv": "Negative", "syphilis": "Negative"})
        self.assertEqual(result, "Clean")
        unit = next(row for row in self.db.state()["inventory"] if row["id"] == created["unit_id"])
        self.assertEqual(unit["status"], "Available")

    def test_patient_lab_order_is_persisted(self):
        order_id = self.db.add_lab_order({"patient": "Patient Test", "patientCode": "PT-X", "symptoms": "Fatigue", "testType": "CBC + Ferritin", "doctor": "Dr. Test"})
        self.assertTrue(any(row["id"] == order_id for row in self.db.state()["labOrders"]))

    def test_unit_cannot_be_reserved_twice(self):
        self.assertTrue(self.db.reserve("LF-2049", "REQ-1043"))
        self.assertFalse(self.db.reserve("LF-2049", "REQ-1043"))
        unit = next(row for row in self.db.state()["inventory"] if row["id"] == "LF-2049")
        self.assertEqual(unit["status"], "Reserved")


if __name__ == "__main__":
    unittest.main()
