from charm.toolbox.pairinggroup import PairingGroup
from vds.storage.memstore import MemStore
from vds.acc.vds_acc import VDSACC


def test_old_proof_fails_after_update():
    grp = PairingGroup('MNT224')
    store = MemStore()
    vds = VDSACC(store, grp)
    pub, st = vds.setup()

    vds.append(st, b"hello")
    vds.append(st, b"world")

    old_proof = vds.query(1)
    assert vds.verify(pub, 1, b"hello", old_proof)

    # update index 1
    ur = vds.update(st, 1, b"HELLO")
    pub.accumulator = ur.root.value

    # old proof should fail now
    assert not vds.verify(pub, 1, b"hello", old_proof)

    # new proof passes
    new_proof = vds.query(1)
    assert vds.verify(pub, 1, b"HELLO", new_proof)
