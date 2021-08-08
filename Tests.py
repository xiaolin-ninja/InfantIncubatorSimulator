#Vulnerability Name - Authentication available
import socket

infPort = 23456
incPort = 23457
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
BUG I: can run commands without authenticating
"""

# tests command chaining does not work with AUTH or LOGOUT

try:
    resp = send_command(b"AUTH foo;GET_TEMP", incPort)
    assert(resp in error_messages) # test should fail because of bug
except Exception as x:
    print(x)
    assert(1==2)

try:
    resp = send_command(b"LOGOUT bar;GET_TEMP", incPort)
    assert(resp in error_messages) # test should fail because of bug
except Exception as x:
    print(x)
    assert(1==2)

try:
    token = authenticate(incPort, b"!Q#E%T&U8i6y4r2w")
    resp = send_command(b"%s;GET_TEMP;LOGOUT %s" % token, token, incPort)
    assert(resp in error_messages)
except Exception as x:
    print(x)
    assert(1==2)


"""
BUG II : setting temperature to C or F breaks temperature calculations in the Incubator temperature,
and makes the temperature line disappear in client.
(It does not cause the same inconsistency with the Infant temperature)
"""

# See Vulnerability.txt for explanation of this bug and fix.


"""
BUG III: race condition
"""

# See Vulnerability.txt for explanation of this bug and fix.

# ------------------------- TESTS ---------------------------- #

# Test authentication works

try:
    token = authenticate(incPort, b"!Q#E%T&U8i6y4r2w")
    assert(token != None)
except Exception as x:
    print(x)
    assert(1==2)

# Test command works with auth key
try:
    token = authenticate(infPort, b"!Q#E%T&U8i6y4r2w")
    resp = send_command(b"%s;GET_TEMP" % token, infPort)
    assert(resp not in error_messages)
except Exception as x:
    print(x)
    assert(1==2)

# Test command chaining works with auth key
try:
    token = authenticate(infPort, b"!Q#E%T&U8i6y4r2w")
    resp = send_command(b"%s;SET_DEGC;GET_TEMP" % token, infPort)
    assert(resp not in error_messages)
except Exception as x:
    print(x)
    assert(1==2)

# Test commands no longer work after logout
try:
    token = authenticate(infPort, b"!Q#E%T&U8i6y4r2w")
    send_command(b"LOGOUT %s" % token, infPort)
    resp = send_command(b"%s;GET_TEMP" % token, infPort)
    assert(resp in error_messages)
except Exception as x:
    print(x)
    assert(1==2)