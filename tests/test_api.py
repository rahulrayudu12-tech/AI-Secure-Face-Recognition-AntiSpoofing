import unittest
import json
from backend.app import create_app

class TestFlaskEndpoints(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_health_check(self):
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(data["status"], "healthy")

    def test_dashboard_stats(self):
        resp = self.client.get("/api/dashboard/stats")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(data["status"], "success")
        self.assertIn("total_users", data["data"])

    def test_register_and_login(self):
        email = "test_user_unique@auraid.cyber"
        # Register
        reg_resp = self.client.post("/api/register", json={
            "name": "Unit Tester",
            "email": email,
            "password": "Password123!"
        })
        self.assertIn(reg_resp.status_code, [201, 409])

        # Login
        login_resp = self.client.post("/api/login", json={
            "email": email,
            "password": "Password123!"
        })
        self.assertEqual(login_resp.status_code, 200)
        data = json.loads(login_resp.data)
        self.assertIn("token", data)

if __name__ == "__main__":
    unittest.main()
