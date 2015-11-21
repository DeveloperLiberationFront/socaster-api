from __future__ import print_function
import subprocess,time,sys,threading

"""
This script runs both the server (run.py) and the tests (tests.py). It first
launches the server, waits a couple seconds for it to start, and then runs
the tests.

It is mainly meant for use in a CI environment. Since output (and errors)
from both the server and the tests is written simultaneously to stdout,
each line is prefixed with SERVER for lines from the server, and TESTS for
lines from the tests.

Note that because the server and the tests run in parallel, the order of the
outputs may not always be the actual order of execution. Expect to see things
like errors in the tests before the request is shown in the server.
"""

def print_output(prefix, pipe):
    for line in pipe:
        print("{}: {}".format(prefix, line), end="")

if __name__ == "__main__":
    print("Launching server")
    server = subprocess.Popen(["python", "run.py"],
                              stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT)
    t1 = threading.Thread(target=print_output,
                          args=("SERVER", server.stdout))
    t1.start()
    time.sleep(2)

    if server.poll() is not None:
        print("Server didn't start correctly")
        sys.exit(1)

    print("Server launched. Running tests.")
    try:
        tests = subprocess.Popen(["python", "tests.py"],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT)
        t2 = threading.Thread(target=print_output,
                              args=("TESTS", tests.stdout))
        t2.start()
        sys.exit(tests.wait())
    finally:
        print("Killing server")
        server.kill()
