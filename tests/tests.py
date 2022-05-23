import unittest
from app import world_backup as wb


class MyTestCase(unittest.TestCase):
    def test_something(self):
        # self.assertEqual(True, False)
        # print(f"root = {wb.script_root()}")
        # print("nothing configured to test.py")
        print(f"root = {wb.ROOT}")


if __name__ == '__main__':
    unittest.main()
