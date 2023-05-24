
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


class RoundRobin:
    def __init__(self):
        self.next_server = {}

    
    def get_next_server(self, port: int):
        if port not in self.next_server:
            self.next_server[port] = 0
            return services[port]["servers"][0]

        self.next_server[port] = (self.next_server[port] + 1) % len(services[port]["servers"])
        return self.next_server[port]
        
