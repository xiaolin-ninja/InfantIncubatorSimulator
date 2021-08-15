#Vulnerability Name - Authentication available
import socket

infPort = 23456
incPort = 23457
secret_key = b"!Q#E%T&U8i6y4r2w"
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

"""
BUG I: able to delete session tokens without authentication or authorization
"""

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

# tests command chaining does not work with AUTH

try:
    resp = send_command(b"AUTH foo;GET_TEMP", incPort)
    assert(resp == b"Invalid Key") # test should fail because of bug
except Exception as x:
    print(x)
    assert(1==2)

"""
BUG III : setting temperature to C or F breaks temperature calculations in the Incubator temperature,
and makes the temperature line disappear in client.
(It does not cause the same inconsistency with the Infant temperature)
"""

# It's a bit convoluted to test this programatically, so there is detailed manual testing described in Vulnerability.txt.

try:
    token = authenticate(incPort, secret_key)
    temp_C1 = send_command(b"%s;SET_DEGC;GET_TEMP" % token)
    temp_C2 = send_command(b"%s;SET_DEGK;SET_DEGF;SET_DEGC;GET_TEMP" % token)

    # assert that there is not a great temperature difference
    # this test will fail if bug is not fixed
    assert(temp_C2 - temp_C1 < 5)
except Exception as x:
    print(x)
    assert(1==2)


# ------------------------- TESTS ---------------------------- #

# Test authentication works

try:
    token = authenticate(incPort, secret_key)
    assert(token != None)
except Exception as x:
    print(x)
    assert(1==2)

# Test command works with auth key
try:
    token = authenticate(infPort, secret_key)
    resp = send_command(b"%s;GET_TEMP" % token, infPort)
    assert(resp not in error_messages)
except Exception as x:
    print(x)
    assert(1==2)

# Test command chaining works with auth key
try:
    token = authenticate(infPort, secret_key)
    resp = send_command(b"%s;SET_DEGC;GET_TEMP" % token, infPort)
    assert(resp not in error_messages)
except Exception as x:
    print(x)
    assert(1==2)

# Test commands no longer work after logout
try:
    token = authenticate(infPort, secret_key)
    send_command(b"LOGOUT %s" % token, infPort)
    resp = send_command(b"%s;GET_TEMP" % token, infPort)
    assert(resp in error_messages)
except Exception as x:
    print(x)
    assert(1==2)