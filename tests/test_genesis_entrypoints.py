import subprocess
import sys

def test_notice_is_silent():
    res = subprocess.run([sys.executable, "-c", "import omnibridge._genesis; omnibridge._genesis.print_upgrade_notice()"], capture_output=True, text=True)
    assert res.stderr == ""
    assert res.stdout == ""
    import omnibridge._genesis
    assert omnibridge._genesis.NOTICE == ""
