from vds.common.encoding import encode_item, decode_item
from vds.common import sig


def test_encode_decode_roundtrip():
    data = b"abc"
    tag = b"tag"
    idx = 42
    b = encode_item(data, tag, idx)
    d2, t2, i2 = decode_item(b)
    assert d2 == data and t2 == tag and i2 == idx


def test_ed25519_sign_verify():
    sk, vk = sig.keygen()
    msg = b"hello"
    s = sig.sign(sk, msg)
    assert sig.verify(vk, msg, s)
    assert not sig.verify(vk, msg + b"!", s)

