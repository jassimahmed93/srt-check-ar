import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parent


class CommandLineTests(unittest.TestCase):
    def run_checker(self, file, *options):
        return subprocess.run(
            [sys.executable, str(PROJECT / "srt_check.py"), str(file), *options],
            capture_output=True,
            text=True,
            check=False,
        )

    def run_with_file(self, content, *options):
        with tempfile.TemporaryDirectory() as temporary:
            file = Path(temporary) / "subtitle.srt"
            file.write_bytes(content.encode("utf-8-sig"))
            return self.run_checker(file, *options)

    def test_arabic_example_passes(self):
        result = self.run_checker(PROJECT / "example.srt")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("2 cue(s), 0 issue(s).", result.stdout)

    def test_counts_visible_arabic_letters_in_bom_crlf_file(self):
        result = self.run_with_file(
            "1\r\n00:00:00,000 --> 00:00:02,000\r\n<i>مَ</i>\u200f\r\n",
            "--max-chars", "1",
        )
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_reports_overlap_and_readability_issues(self):
        result = self.run_with_file(
            "1\n00:00:00,000 --> 00:00:02,000\nمقطع\n\n"
            "2\n00:00:01,000 --> 00:00:01,100\nسطر طويل\nثانٍ\nثالث\n",
            "--max-chars", "5",
        )
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("Timing overlaps cue on line 1", result.stdout)
        self.assertIn("Line has 8 characters", result.stdout)
        self.assertIn("Cue has 3 lines", result.stdout)
        self.assertIn("Reading speed is", result.stdout)

    def test_reports_malformed_and_zero_length_timings(self):
        result = self.run_with_file(
            "1\ninvalid timing\nمقطع\n\n2\n00:00:02,000 --> 00:00:02,000\n",
        )
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("Invalid timing", result.stdout)
        self.assertIn("End time must come after start time", result.stdout)
        self.assertIn("no visible subtitle text", result.stdout)

    def test_invalid_limit_is_a_usage_error(self):
        result = self.run_checker(PROJECT / "example.srt", "--max-cps", "0")
        self.assertEqual(result.returncode, 2)
        self.assertIn("expected a positive integer", result.stderr)


if __name__ == "__main__":
    unittest.main()
