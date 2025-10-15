import pytest
from charm.toolbox.pairinggroup import PairingGroup
from vds.cvc.vds_cvc import VDSCVC, CVCClientState
from vds.storage.memstore import MemStore


@pytest.mark.xfail(reason="CVC 内部节点配对等式实现仍在完善中，当前验证未开启")
def test_vds_cvc_append_query_verify():
    # CVC 构造采用对称配对群以简化实现（G1×G1）。
    grp = PairingGroup('SS512')
    store = MemStore()
    v = VDSCVC(store, grp, q=8)
    st, _ = v.setup()

    # append a few leaves
    v.append(st, b"item-1")
    v.append(st, b"item-2")
    v.append(st, b"item-3")
    v.append(st, b"item-4")

    # query and verify index 3
    proof = v.query(3)
    assert v.verify(st, 3, b"item-3", proof)
