#Vulnerability Name - Authentication available
import socket

infPort = 23456
incPort = 23457
server = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

def authenticate(p, pw) :
    server.sendto(b"AUTH %s" % pw, ("127.0.0.1", p))
    msg, addr = server.recvfrom(1024)
    return msg.strip()

def send_command(cmd, p):
    server.sendto(cmd, ("127.0.0.1", p))
    msg, addr = server.recvfrom(1024)
    return msg.strip()

# -------------------------------------------------------- #

# Test cannot run commands without authenticating

# try:
#     resp = send_command(b"GET_TEMP potato", infPort)
#     assert(resp == b"Authenticate First")
# except Exception as x:
#     print(x)
#     assert(1==2)

# Test command works with auth key
try:
    resp = send_command(b"GET_TEMP;!Q#E%T&U8i6y4r2w", infPort)
    print(resp)
    assert(resp == b"Authenticate First")
except Exception as x:
    print(x)
    assert(1==2)

# Test authentication works

# try:
#     authenticate(incPort, b"!Q#E%T&U8i6y4r2w")
#     assert(incToken != None)
#     except Exception as ex:
#         print(ex)
#         assert(1==2)

# Test once authenticated, commands work



# def set_temperature(p, pw)

# test SampleNetworkServer has authentication
# try:
#     infPort = 23456
#     incPort = 23457
#     incToken = authenticate(incPort, b"!Q#E%T&U8i6y4r2w")
#     assert(incToken != None)
# except Exception as ex:
#     print(ex)
#     assert(1==2)


# # Blank message
# try:
#     infPort = 23456
#     incPort = 23457
#     s = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
#     s.sendto(b";", ("127.0.0.1", 23457))

#     # incToken = authenticate(incPort, b"potato")
#     # assert(incToken != None)
# except Exception as ex:
#     print(ex)
#     assert(1==2)
