from charm.toolbox.pairinggroup import PairingGroup
from vds.storage.memstore import MemStore
from vds.acc.vds_acc import VDSACC


def test_export_import_roundtrip():
    grp = PairingGroup('MNT224')
    store = MemStore()
    vds = VDSACC(store, grp)
    pub, st = vds.setup()

    vds.append(st, b"x")
    vds.append(st, b"y")
    blob = vds.export_state(st)

    # new store simulates restart; also migrate items
    store2 = MemStore()
    vds2 = VDSACC(store2, grp)
    # migrate saved items
    for idx in (1, 2):
        data, tag, i, sigma = store.get_acc_item(idx)
        store2.save_acc_item(idx, data, tag, sigma)
    # reuse pub, import state
    st2 = vds2.import_state(st, blob)

    # Query should work the same
    q = vds2.query(1)
    assert vds2.verify(pub, 1, b"x", q)
