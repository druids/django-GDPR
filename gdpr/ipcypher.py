"""
Implementation of ipcipher.

https://github.com/PowerDNS/ipcipher

IPv4 took from https://github.com/veorq/ipcrypt/blob/939549e3f542c7ae9eb1aec96164f19b5f9fc46c/ipcrypt.py under CC0
"""

# type: ignore
# flake8: noqa
from hashlib import pbkdf2_hmac
from ipaddress import IPv4Address, IPv6Address, ip_address
from typing import Union

from pyaes import AESModeOfOperationECB


__all__ = ['derive_key', 'encrypt_ipv4', 'decrypt_ipv4', 'encrypt_ipv6', 'decrypt_ipv6', 'encrypt_ip', 'decrypt_ip']

IPv4Type = Union[str, IPv4Address]
IPv6Type = Union[str, IPv6Address]
IPType = Union[IPv4Type, IPv6Type]


def derive_key(key: str):
    """
    PBKDF2(SHA1, Password, 'ipcipheripcipher', 50000, 16)
    """

    return pbkdf2_hmac('sha1', bytes(key, encoding="utf-8"), bytes('ipcipheripcipher', encoding='utf-8'), 50000, 16)


def rotl(b, r):
    return ((b << r) & 0xff) | (b >> (8 - r))


def permute_fwd(state):
    (b0, b1, b2, b3) = state
    b0 += b1
    b2 += b3
    b0 &= 0xff
    b2 &= 0xff
    b1 = rotl(b1, 2)
    b3 = rotl(b3, 5)
    b1 ^= b0
    b3 ^= b2
    b0 = rotl(b0, 4)
    b0 += b3
    b2 += b1
    b0 &= 0xff
    b2 &= 0xff
    b1 = rotl(b1, 3)
    b3 = rotl(b3, 7)
    b1 ^= b2
    b3 ^= b0
    b2 = rotl(b2, 4)
    return b0, b1, b2, b3


def permute_bwd(state):
    (b0, b1, b2, b3) = state
    b2 = rotl(b2, 4)
    b1 ^= b2
    b3 ^= b0
    b1 = rotl(b1, 5)
    b3 = rotl(b3, 1)
    b0 -= b3
    b2 -= b1
    b0 &= 0xff
    b2 &= 0xff
    b0 = rotl(b0, 4)
    b1 ^= b0
    b3 ^= b2
    b1 = rotl(b1, 6)
    b3 = rotl(b3, 3)
    b0 -= b1
    b2 -= b3
    b0 &= 0xff
    b2 &= 0xff
    return b0, b1, b2, b3


def xor4(x, y):
    return [(x[i] ^ y[i]) & 0xff for i in (0, 1, 2, 3)]


def encrypt_ipv4_bytes_key(key: bytes, ip: IPv4Address) -> str:
    """16-byte key, ip string like '192.168.1.2'"""
    if ip.version != 4:
        raise ValueError('IPv6 supplied to IPv4 function.')
    k = [int(x) for x in key]
    try:
        state = [int(x) for x in ip.exploded.split('.')]
    except ValueError:
        raise
    try:
        state = xor4(state, k[:4])
        state = permute_fwd(state)
        state = xor4(state, k[4:8])
        state = permute_fwd(state)
        state = xor4(state, k[8:12])
        state = permute_fwd(state)
        state = xor4(state, k[12:16])
    except IndexError:
        raise
    return '.'.join(str(x) for x in state)


def encrypt_ipv4(key: str, ip: IPv4Type) -> str:
    if not isinstance(ip, IPv4Address):
        ip = ip_address(ip)
    return encrypt_ipv4_bytes_key(derive_key(key), ip)  # type: ignore


def decrypt_ipv4_bytes_key(key: bytes, ip: IPv4Address) -> str:
    """16-byte key, encrypted ip string like '215.51.199.127'"""
    if ip.version != 4:
        raise ValueError('IPv6 supplied to IPv4 function.')
    k = [x for x in key]
    try:
        state = [int(x) for x in ip.exploded.split('.')]
    except ValueError:
        raise
    try:
        state = xor4(state, k[12:16])
        state = permute_bwd(state)
        state = xor4(state, k[8:12])
        state = permute_bwd(state)
        state = xor4(state, k[4:8])
        state = permute_bwd(state)
        state = xor4(state, k[:4])
    except IndexError:
        raise
    return '.'.join(str(x) for x in state)


def decrypt_ipv4(key: str, ip: IPv4Type) -> str:
    if not isinstance(ip, IPv4Address):
        ip = ip_address(ip)
    return decrypt_ipv4_bytes_key(derive_key(key), ip)


def encrypt_ipv6_bytes_key(key: bytes, ip: IPv6Address) -> IPv6Address:
    return IPv6Address(AESModeOfOperationECB(key).encrypt(ip.packed))


def encrypt_ipv6(key: str, ip: IPv6Type) -> str:
    if not isinstance(ip, IPv6Address):
        ip = ip_address(ip)
    return encrypt_ipv6_bytes_key(derive_key(key), ip).compressed


def decrypt_ipv6_bytes_key(key: bytes, ip: IPv6Address) -> IPv6Address:
    return IPv6Address(AESModeOfOperationECB(key).decrypt(ip.packed))


def decrypt_ipv6(key: str, ip: IPv6Type) -> str:
    if not isinstance(ip, IPv6Address):
        ip = ip_address(ip)
    return decrypt_ipv6_bytes_key(derive_key(key), ip).compressed


def encrypt_ip(key: str, ip: IPType) -> str:
    if not isinstance(ip, IPv6Address) and not isinstance(ip, IPv4Address):
        ip = ip_address(ip)
    if ip.version == 4:
        return encrypt_ipv4(key, ip)
    elif ip.version == 6:
        return encrypt_ipv6(key, ip)


def decrypt_ip(key: str, ip: IPType) -> str:
    if not isinstance(ip, IPv6Address) and not isinstance(ip, IPv4Address):
        ip = ip_address(ip)
    if ip.version == 4:
        return decrypt_ipv4(key, ip)
    elif ip.version == 6:
        return decrypt_ipv6(key, ip)
