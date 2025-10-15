from charm.toolbox.pairinggroup import PairingGroup
from vds.storage.memstore import MemStore
from vds.acc.vds_acc import VDSACC


def test_vds_acc_end_to_end():
    grp = PairingGroup('MNT224')
    store = MemStore()
    vds = VDSACC(store, grp)
    pub, st = vds.setup()

    # append a few items
    r1 = vds.append(st, b"a" * 10)
    r2 = vds.append(st, b"b" * 10)
    r3 = vds.append(st, b"c" * 10)

    # query idx=2 and verify
    q = vds.query(2)
    assert vds.verify(pub, 2, b"b" * 10, q)

    # update idx=2
    ur = vds.update(st, 2, b"B" * 12)
    # update public accumulator root
    pub.accumulator = ur.root.value

    # new query should verify
    q2 = vds.query(2)
    assert vds.verify(pub, 2, b"B" * 12, q2)
