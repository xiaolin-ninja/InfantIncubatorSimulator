import socket
import ssl
import os
from dotenv import load_dotenv

infPort = 23456
incPort = 23457
secret_key = b'!Q#E%T&U8i6y4r2w'
server = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
error_messages = [b"Authenticate First", b"Bad Command", b"Bad Token", b"Invalid Key", b"Invalid Command"]

def authenticate(p, pw) :
    server.sendto(b"AUTH %s" % pw, ("127.0.0.1", p))
    msg, addr = server.recvfrom(1024)
    return msg.strip()

def send_command(cmd, p):
    server.sendto(cmd, ("127.0.0.1", p))
    msg, addr = server.recvfrom(1024)
    return msg.strip()

# ------------------------ EXPLOITS -------------------------- #

# Tests are written to fail if bug is not fixed.

"""
BUG I: able to delete session tokens without authentication or authorization
"""

def testcase1():
# tests that LOGOUT [token] cannot be chained
    try:
        token1 = authenticate(infPort, secret_key)
        token2 = authenticate(infPort, secret_key)
        token3 = authenticate(infPort, secret_key)
        cmd = "{0};LOGOUT {1};LOGOUT {2}".format(token1, token2, token3).encode('utf-8')
        resp = send_command(cmd, infPort)

        assert(resp in error_messages)
    except Exception as ex:
        print (ex)
        assert(1 == 2)

    ## tests ideal behavior of LOGOUT mechanism

    # fails without valid session and old UI
    try:
        token = authenticate(infPort, secret_key)
        resp = send_command(b"LOGOUT %s" % token, infPort)
        assert(resp in error_messages)
    except Exception as ex:
        print (ex)
        assert(1 == 2)

    # works with valid session and new UI
    try:
        token = authenticate(incPort, secret_key)
        resp = send_command(b"%s;LOGOUT" % token, incPort)
        assert(resp == b"Logged Out")
    except Exception as ex:
        print (ex)
        assert(1 == 2)

"""
BUG II: Access Control failure: can run commands without authenticating
"""

def testcase2():
# tests command chaining does not work with AUTH
    try:
        resp = send_command(b"AUTH foo;GET_TEMP", incPort)
        assert(resp == b"Invalid Key") # test should fail because of bug
    except Exception as x:
        print(x)
        assert(1==2)

"""
BUG III: setting temperature to C or F breaks temperature calculations in the Incubator temperature,
and makes the temperature line disappear in client.
(It does not cause the same inconsistency with the Infant temperature)
"""

# It's a bit convoluted to test this programatically, so there is detailed manual testing described in Vulnerability.txt.

def testcase3():
# assert that there is not a great temperature difference after converting between K, F, C     
    try:
        token = authenticate(incPort, secret_key)
        temp_C1 = send_command(b"%s;SET_DEGC;GET_TEMP" % token, incPort)
        temp_C2 = send_command(b"%s;SET_DEGK;SET_DEGF;SET_DEGC;GET_TEMP" % token, incPort)

        assert(float(temp_C2) - float(temp_C1) < 5)
    except Exception as x:
        print(x)
        assert(1==2)

"""
VULNERABILIITY IV and V: hard-coded credentials in source code
"""

def testcase4():
    try:
        with open('./SampleNetworkServer.py') as f:
            assert('!Q#E%T&U8i6y4r2w' not in f.read())
    except Exception as ex:
        print (ex)
        assert(1 == 2)


def testcase5():
    try:
        with open('./SampleNetworkClient.py') as f:
            assert('!Q#E%T&U8i6y4r2w' not in f.read())
    except Exception as ex:
        print (ex)
        assert(1 == 2)


"""
VULNERABILITY VI: plaintext passwords and tokens over network traffic

This test also lives in TLSTests.py, and will only work with TLSNetworkServer.py.
"""

def testcase6():
# tests for valid TLS
    try:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_verify_locations('./infinc.crt')

        tls_server = ssl.wrap_socket(server)
        token = authenticate(incPort, secret_key)

        tls_server.sendto(b"%s;GET_TEMP" % token, ("127.0.0.1", p))
        msg, addr = tls_server.recvfrom(1024)

        m = float(msg.decode("utf-8"))
        # will fail if response is encrypted and cannot be converted to a float
        print(m)
        assert (not isinstance(m, float))
    except Exception as ex:
        print(ex)
        assert (1 == 2)



# --------------------------------------------------------------------------- #

def main():
    testcases = {
        '1': testcase1,
        '2': testcase2,
        '3': testcase3,
        '4': testcase4,
        '5': testcase5,
        'exit': exit
    }

    while True:
        print("Type 'A' to run all tests, or select from 1-5.")
        cmd = input()
        if cmd == "A":
            for i in range(1,6):
                testcases.get(str(i))()
            break
        else:
            if cmd in testcases:
                testcases.get(cmd)()


main()