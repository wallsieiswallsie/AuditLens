import unittest
from audit_engine.__main__ import health

class HealthTest(unittest.TestCase):
    def test_health_contract(self):
        result = health()
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["service"], "auditlens-engine")
        self.assertTrue(result["pandas_version"])

if __name__ == "__main__":
    unittest.main()

