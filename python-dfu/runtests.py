import pytest
import sys

def runTests():
    return pytest.main(["-x","test","--cov",".", "--cov-report", "html", "--cov-config",".coveragec", "--cov-branch"])



if __name__ == "__main__":
    sys.exit(runTests())