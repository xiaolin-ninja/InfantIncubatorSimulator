import ssl
import socket
import os
from dotenv import load_dotenv

infPort = 23456
incPort = 23457
secret_key = b'!Q#E%T&U8i6y4r2w'
server = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)


def testcase6():
# tests for valid TLS. In this case, if the test fails, that is the success case.
    try:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_verify_locations('./infinc.crt')

        with socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM) as sock:
            s = ssl.wrap_socket(sock)
            s.connect(('', incPort))
            token = s.send(b"AUTH %s" % secret_key)
            # will fail if token is not returned as plaintext
            s.send(b"%s;GET_TEMP" % token)

            msg = s.rec(1024)
            m = float(msg.decode("utf-8"))
            # will fail if response is encrypted and cannot be converted to a float
            print(m)
            assert (not isinstance(m, float))
    except Exception as ex:
        print(ex)

testcase6()