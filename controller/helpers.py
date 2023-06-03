
import socket
import fcntl
import struct
from config import *


def get_interface_ip(interface: str):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ip = socket.inet_ntoa(fcntl.ioctl(s.fileno(),  0x8915, struct.pack(
        '256s', bytes(interface, 'utf-8')[:15]))[20:24])

    return ip


def printGrpcError(e):
    print("gRPC Error:", e.details(), end=' ')
    status_code = e.code()
    print("(%s)" % status_code.name, end=' ')



