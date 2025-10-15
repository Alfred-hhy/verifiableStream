import subprocess
import sys


def test_cli_help_runs():
    proc = subprocess.run([sys.executable, "-m", "vds.cli.vds_cli", "--help"], capture_output=True)
    assert proc.returncode == 0

