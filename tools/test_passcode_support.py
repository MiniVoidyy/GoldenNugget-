"""Offline checks for the Passcode Theme version gate."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.devicemanagement.passcode_support import passcode_theme_unavailable_reason


class PasscodeSupportTests(unittest.TestCase):
    def test_passcode_version_boundary(self):
        allowed = [('27.0', '24A435'), ('27.0.1', '24A500'), ('27.1', '24B1'),
                   ('27.2', '24B5084k'), ('27.2', '24B5089g'), ('27.2', '24B5099f')]
        blocked = [('26.6', '23G1'), ('27.2', '24B5110a'), ('27.2', '24B100'),
                   ('27.2', ''), ('27.2.1', '24B5099f'), ('27.3', '24C1'), ('unknown', '')]
        for version, build in allowed:
            with self.subTest(version=version, build=build):
                self.assertIsNone(passcode_theme_unavailable_reason(version, build, 'iPhone17,3'))
        for version, build in blocked:
            with self.subTest(version=version, build=build):
                self.assertIsNotNone(passcode_theme_unavailable_reason(version, build, 'iPhone17,3'))
        self.assertIsNotNone(passcode_theme_unavailable_reason('27.0', '24A435', 'iPad16,3'))
        self.assertIsNotNone(passcode_theme_unavailable_reason('', '', ''))



if __name__ == '__main__':
    unittest.main()
