import random
from charm.toolbox.pairinggroup import PairingGroup
from vds.cvc.vds_cvc import VDSCVC
from vds.storage.memstore import MemStore


def test_vds_cvc_update_flow():
    grp = PairingGroup('SS512')
    store = MemStore()
    v = VDSCVC(store, grp, q=8)
    st, _ = v.setup()

    N = 32
    items = [random.randbytes(16) for _ in range(N)]
    for d in items:
        v.append(st, d)

    # pick 5 random updates
    for _ in range(5):
        idx = random.randint(1, N)
        new_data = random.randbytes(24)
        ur = v.update(st, idx, new_data)
        proof = v.query(idx)
        assert v.verify(st, idx, new_data, proof)

