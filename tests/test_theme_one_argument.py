"""tools/theme.sh reads one shape per run: a theme folder, --as <name> <folder>, --list, --remove <name>, or --reset.

The first word alone used to decide everything the script did: `if [ "${1:-}" = --reset ]` took the reset branch
and nothing else was read. So the undo hint the script prints, "Undo with: tools/theme.sh --reset", with the
folder appended - `theme.sh --reset themes/aurora` - matched that branch on the first word and threw the folder
away: the theme the reader named was removed from the TV instead of pushed, and the run answered "reset" with
exit 0, so nothing in it said the folder had not been used. The same line the other way round,
`theme.sh themes/aurora --reset`, pushed the theme and ignored the --reset, which is the one word that asked for
it to be removed. A second folder, `theme.sh themes/a themes/b`, pushed only a.

Every shape is listed in one case statement now, read before TV_HOST is required and before anything is sent.
A line that fits none of them ends with "Nothing was sent to the TV." on exit 2, and a command line with no
argument gets the usage line instead of bash's own "THEME_ARG: usage: ..." out of the `${THEME_ARG:?}` expansion.
The bundle flags make the same promise: --as takes a name and a folder, --remove one name, and a --reset,
--list or folder beside either is refused rather than dropped.

These tests run the real tools/theme.sh against a stub tools/tv.py that appends every call to a log and exits
0, so "nothing was sent to the TV" means the log is not there, and "the theme is still pushed" means the log
holds the config.json push. A theme folder with a config.json is written in the test.

Run from the repository root: python3 -m unittest discover -s tests -v
"""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
USAGE = "usage: theme.sh <theme folder> | --as <name> <theme folder> | --list | --remove <name> | --reset"
REFUSAL = "Nothing was sent to the TV."

# Every call theme.sh (and theme_restart.py) makes reaches this file, so a test can tell whether anything was
# asked of the TV. The real client is never imported: the tools are copied into a folder of the test's own.
FAKE_TV = '''\
import os
import sys
with open(os.environ["FAKE_LOG"], "a") as log:
    log.write(" ".join(sys.argv[1:]) + "\\n")
sys.exit(0)
'''


class ThemeScriptTest(unittest.TestCase):
    """A copy of the tools beside a stub tv.py, so a run can only reach the TV through the log."""

    def setUp(self):
        self.base = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.base, ignore_errors=True)
        self.tools = self.base / "tools"
        self.tools.mkdir()
        for name in ("theme.sh", "theme_restart.py"):
            shutil.copy2(TOOLS / name, self.tools / name)
        (self.tools / "tv.py").write_text(FAKE_TV)
        venv = self.tools / "venv" / "bin"
        venv.mkdir(parents=True)
        (venv / "python").symlink_to(sys.executable)
        self.theme = self.base / "my-theme"
        self.theme.mkdir()
        (self.theme / "config.json").write_text('{"background_color": "#000000"}\n', encoding="utf-8")
        self.other = self.base / "another-theme"
        self.other.mkdir()
        (self.other / "config.json").write_text('{"background_color": "#ffffff"}\n', encoding="utf-8")
        self.log = self.base / "tv-calls.log"

    def run_theme(self, *args):
        if os.name != "posix" or not shutil.which("bash"):
            raise unittest.SkipTest("theme.sh is a POSIX script; it needs bash")
        env = {k: v for k, v in os.environ.items() if k != "TV_HOST"}
        env.update({"TV_HOST": "192.0.2.10", "FAKE_LOG": str(self.log)})
        return subprocess.run(["bash", str(self.tools / "theme.sh"), *args], env=env,
                              capture_output=True, text=True, timeout=120)

    def tv_calls(self):
        if not self.log.exists():
            return []
        return [line for line in self.log.read_text().splitlines() if line.strip()]

    def assert_refused(self, result, word):
        self.assertEqual(2, result.returncode, result.stdout + result.stderr)
        self.assertEqual("", result.stdout, "a refusal writes nothing on stdout")
        self.assertIn(word, result.stderr, "the message has to name the word that was not used")
        self.assertIn(REFUSAL, result.stderr, result.stderr)
        self.assertNotIn("Traceback", result.stderr, result.stderr)
        self.assertEqual([], self.tv_calls(), "a refused command line asked the TV for something")


class ThemeOneArgumentTest(ThemeScriptTest):
    def test_reset_with_a_theme_folder_is_refused(self):
        # The defect: this line removes the theme the TV has and never pushes the folder it was given.
        self.assert_refused(self.run_theme("--reset", str(self.theme)), str(self.theme))

    def test_a_flag_after_the_folder_is_refused(self):
        # The other order: the theme is pushed and the --reset is dropped, so the theme it asked to remove stays.
        self.assert_refused(self.run_theme(str(self.theme), "--reset"), "--reset")

    def test_a_second_theme_folder_is_refused(self):
        self.assert_refused(self.run_theme(str(self.theme), str(self.other)), str(self.other))

    def test_store_with_a_second_folder_is_refused(self):
        self.assert_refused(self.run_theme("--as", "japan", str(self.theme), str(self.other)), str(self.other))

    def test_store_with_a_reset_is_refused(self):
        self.assert_refused(self.run_theme("--reset", "--as", "japan", str(self.theme)), "--as")

    def test_list_with_anything_else_is_refused(self):
        self.assert_refused(self.run_theme("--list", str(self.theme)), str(self.theme))

    def test_remove_without_a_name_gets_the_usage_line(self):
        result = self.run_theme("--remove")
        self.assertEqual(2, result.returncode, result.stdout + result.stderr)
        self.assertIn(USAGE, result.stderr, result.stderr)
        self.assertEqual([], self.tv_calls())

    def test_no_argument_gets_the_usage_line(self):
        result = self.run_theme()
        self.assertEqual(2, result.returncode, result.stdout + result.stderr)
        self.assertEqual("", result.stdout)
        self.assertIn(USAGE, result.stderr, result.stderr)
        self.assertNotIn("THEME_ARG", result.stderr, "bash's own expansion error is not the usage line")
        self.assertEqual([], self.tv_calls())

    def test_reset_alone_still_resets(self):
        result = self.run_theme("--reset")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("reset", result.stdout)
        calls = self.tv_calls()
        self.assertTrue(calls, "the reset asks the TV to remove the overlay")
        self.assertTrue(any("config.json" in line and "rm -f" in line for line in calls),
                        "the reset has to remove the theme's config.json")

    def test_a_folder_alone_still_pushes(self):
        result = self.run_theme(str(self.theme))
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("is on the TV", result.stdout)
        pushes = [line for line in self.tv_calls() if line.startswith("--push")]
        self.assertTrue(pushes, "the theme's config.json is pushed")
        self.assertTrue(any(str(self.theme / "config.json") in line for line in pushes), pushes)


class ThemeBundleArgumentTest(ThemeScriptTest):
    """The bundle flags, on the same stub: a store writes under themes/<name>/ and leaves Home alone."""

    def test_store_writes_one_folder_deeper(self):
        result = self.run_theme("--as", "japan", str(self.theme))
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("stored", result.stdout)
        calls = self.tv_calls()
        self.assertTrue(any("themes/japan/config.json" in line for line in calls), calls)
        self.assertFalse(any(line.startswith("--reboot") for line in calls), "storing a bundle does not restart Home")

    def test_store_refuses_a_name_that_is_not_a_folder(self):
        for name in ("../japan", "ja pan", ".hidden", "japan.theme", ""):
            with self.subTest(name=name):
                self.log.unlink(missing_ok=True)
                result = self.run_theme("--as", name, str(self.theme))
                self.assertEqual(2, result.returncode, result.stdout + result.stderr)
                self.assertIn(REFUSAL, result.stderr, result.stderr)
                self.assertEqual([], self.tv_calls(), "a refused name reached the TV")

    def test_store_without_a_folder_gets_the_usage_line(self):
        result = self.run_theme("--as", "japan")
        self.assertEqual(2, result.returncode, result.stdout + result.stderr)
        self.assertIn(USAGE, result.stderr, result.stderr)
        self.assertEqual([], self.tv_calls())

    def test_list_reads_the_bundle_folders(self):
        result = self.run_theme("--list")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("no theme bundles on the TV", result.stdout)
        self.assertTrue(any("themes/*/" in line for line in self.tv_calls()), self.tv_calls())

    def test_remove_deletes_the_bundle_and_restarts_home(self):
        result = self.run_theme("--remove", "japan")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("removed", result.stdout)
        calls = self.tv_calls()
        self.assertTrue(any("rm -rf" in line and "themes/japan" in line for line in calls), calls)

    def test_remove_refuses_a_name_that_is_not_a_folder(self):
        self.assert_refused(self.run_theme("--remove", "../japan"), "../japan")


class ThemeArgumentSourceTest(unittest.TestCase):
    """The judgement sits where a command line cannot reach the TV, and the Windows twin carries it too."""

    def setUp(self):
        self.shell = (TOOLS / "theme.sh").read_text(encoding="utf-8")
        self.ps = (TOOLS / "theme.ps1").read_text(encoding="utf-8")

    def test_the_shape_is_judged_before_any_branch_runs_or_sends(self):
        judged = self.shell.index('case "${1:-}" in')
        self.assertLess(judged, self.shell.index('[ "$MODE" = reset ]'),
                        "the reset branch is what dropped the folder, so the shape is read first")
        self.assertLess(judged, self.shell.index('tv "mkdir -p $DIR'),
                        "nothing can be sent before the command line is read")

    def test_the_usage_line_is_ours_not_bash(self):
        self.assertIn('echo "$USAGE" >&2', self.shell)
        self.assertLess(self.shell.index('echo "$USAGE" >&2'), self.shell.index('${THEME_ARG:?'))

    def test_the_windows_twin_refuses_a_mixed_line(self):
        self.assertIn("-Reset takes no other argument", self.ps)
        self.assertIn(REFUSAL, self.ps)
        judged = self.ps.index("if ($Reset) {")
        self.assertLess(judged, self.ps.index('Invoke-Tv tv.py "mkdir -p $dir'),
                        "the reset branch is judged before anything is sent")
        self.assertIn("exit 2", self.ps[judged:])


if __name__ == "__main__":
    unittest.main()
