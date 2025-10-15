from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

import click
import msgpack
from charm.toolbox.pairinggroup import PairingGroup

from ..acc.vds_acc import VDSACC
from ..cvc.vds_cvc import VDSCVC
from ..storage.memstore import MemStore
from ..common.types import ACCPublic, QueryProof, AppendReceipt, UpdateReceipt, RootDigest
from ..common import ser


def _read_data_arg(arg: str) -> bytes:
    p = Path(arg)
    if p.exists() and p.is_file():
        return p.read_bytes()
    # try hex
    s = arg.lower()
    if s.startswith("0x"):
        s = s[2:]
    try:
        return bytes.fromhex(s)
    except Exception:
        return arg.encode()


def _load_state(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return msgpack.unpackb(path.read_bytes(), raw=False)


def _save_state(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(msgpack.packb(obj, use_bin_type=True))


@click.group()
def cli() -> None:
    """vds-cli: ACC/CVC 本地演示 CLI。状态使用 msgpack 文件持久化。"""


@cli.command()
@click.option("--scheme", type=click.Choice(["cvc", "acc"]), required=True)
@click.option("--curve", type=str, default="MNT224", help="配对曲线 (ACC: MNT224; CVC: SS512) 或其他")
@click.option("--q", "q_branch", type=int, default=64, help="CVC 的 q 叉因子")
@click.option("--store", type=click.Path(), required=True, help="状态文件路径 (msgpack)")
def init(scheme: str, curve: str, q_branch: int, store: str) -> None:
    t0 = time.perf_counter()
    path = Path(store)
    grp = PairingGroup(curve if scheme == "acc" else "SS512")
    if scheme == "acc":
        mem = MemStore()
        vds = VDSACC(mem, grp)
        pub, st = vds.setup()
        acc_v, acc_powers = mem.get_acc_state()
        state = {
            "scheme": "acc",
            "curve": curve,
            "pub": pub.model_dump(),
            "client_state": st,
            "store": {
                "acc_value": acc_v,
                "acc_cache": acc_powers,
                "f_coeffs": mem.get_acc_poly(),
                "items": {},
            },
        }
        _save_state(path, state)
    else:
        mem = MemStore()
        vds = VDSCVC(mem, grp, q=q_branch)
        st, _ = vds.setup()
        state = {
            "scheme": "cvc",
            "curve": "SS512",
            "q": q_branch,
            "client_state": {
                "pk": st.pk.model_dump(),
                "sk": st.sk.model_dump(),
                "root": st.root.model_dump(),
                "cnt": st.cnt,
            },
            "items": {},
        }
        _save_state(path, state)
    click.echo(json.dumps({"ok": True, "scheme": scheme, "curve": curve, "store": store, "ms": int((time.perf_counter()-t0)*1000)}))


def _restore_acc(path: Path) -> Tuple[VDSACC, MemStore, ACCPublic, bytes, Dict[str, Any]]:
    obj = _load_state(path)
    assert obj.get("scheme") == "acc"
    grp = PairingGroup(obj["curve"])  # type: ignore[index]
    mem = MemStore()
    mem.set_acc_state(obj["store"]["acc_value"], obj["store"]["acc_cache"])  # type: ignore[index]
    mem.set_acc_poly(obj["store"]["f_coeffs"])  # type: ignore[index]
    for k, v in obj["store"]["items"].items():  # type: ignore[index]
        mem.save_acc_item(int(k), v[0], v[1], v[3])
    vds = VDSACC(mem, grp)
    pub = ACCPublic(**obj["pub"])  # type: ignore[arg-type]
    st = obj["client_state"]  # type: ignore[index]
    return vds, mem, pub, st, obj


def _restore_cvc(path: Path) -> Tuple[VDSCVC, MemStore, Dict[str, Any]]:
    obj = _load_state(path)
    assert obj.get("scheme") == "cvc"
    grp = PairingGroup("SS512")
    mem = MemStore()
    vds = VDSCVC(mem, grp, q=int(obj.get("q", 64)))
    # 通过重放 items 重建状态
    st, _ = vds.setup()
    # 覆盖 sk/pk 以一致（PRF 决定 r）
    st.pk = type(st.pk)(**obj["client_state"]["pk"])  # type: ignore
    st.sk = type(st.sk)(**obj["client_state"]["sk"])  # type: ignore
    st.cnt = 0
    st.root = RootDigest(value=st.root.value)
    # 重放 append
    for idx_str in sorted(obj["items"].keys(), key=lambda x: int(x)):  # type: ignore[index]
        data = obj["items"][idx_str]  # type: ignore[index]
        vds.append(st, data)
    return vds, mem, obj


@cli.command()
@click.option("--scheme", type=click.Choice(["cvc", "acc"]), required=True)
@click.option("--store", type=click.Path(), required=True)
@click.option("--data", type=str, required=True, help="数据（hex|文件路径|直接字符串）")
def append(scheme: str, store: str, data: str) -> None:
    t0 = time.perf_counter()
    path = Path(store)
    buf = _read_data_arg(data)
    if scheme == "acc":
        vds, mem, pub, st, state = _restore_acc(path)
        rec = vds.append(st, buf)
        # 记录 items（注意：从 mem 取最新 idx）
        idx = mem.acc_count()
        d, tag, i, sigma = mem.get_acc_item(idx)
        state["store"]["items"][str(idx)] = [d, tag, i, sigma]
        # 更新根
        state["pub"]["accumulator"] = rec.root.value
        _save_state(path, state)
        click.echo(json.dumps({"ok": True, "index": idx, "root": len(rec.root.value), "ms": int((time.perf_counter()-t0)*1000)}))
    else:
        vds, mem, state = _restore_cvc(path)
        st = type("_ST", (), {})()
        # 构造兼容的 client_state（仅 append 需要 pk/sk/root/cnt）
        from ..common.types import CVCParamsPK, CVCParamsSK
        st.pk = CVCParamsPK(**state["client_state"]["pk"])  # type: ignore[arg-type]
        st.sk = CVCParamsSK(**state["client_state"]["sk"])  # type: ignore[arg-type]
        st.root = RootDigest(**state["client_state"]["root"])  # type: ignore[arg-type]
        st.cnt = int(state["client_state"]["cnt"])  # type: ignore[index]
        rec = vds.append(st, buf)
        idx = st.cnt
        state["client_state"]["root"] = st.root.model_dump()
        state["client_state"]["cnt"] = st.cnt
        state["items"][str(idx)] = buf
        _save_state(path, state)
        click.echo(json.dumps({"ok": True, "index": idx, "root": len(rec.root.value), "ms": int((time.perf_counter()-t0)*1000)}))


@cli.command()
@click.option("--scheme", type=click.Choice(["cvc", "acc"]), required=True)
@click.option("--store", type=click.Path(), required=True)
@click.option("--index", type=int, required=True)
@click.option("--out", type=str, required=False)
def query(scheme: str, store: str, index: int, out: Optional[str]) -> None:
    t0 = time.perf_counter()
    path = Path(store)
    if scheme == "acc":
        vds, mem, pub, st, state = _restore_acc(path)
        pr = vds.query(index)
        if out:
            Path(out).write_bytes(pr.payload)
        click.echo(json.dumps({"ok": True, "scheme": scheme, "index": index, "proof_bytes": len(pr.payload), "ms": int((time.perf_counter()-t0)*1000)}))
    else:
        vds, mem, state = _restore_cvc(path)
        pr = vds.query(index)
        if out:
            Path(out).write_bytes(pr.payload)
        click.echo(json.dumps({"ok": True, "scheme": scheme, "index": index, "proof_bytes": len(pr.payload), "ms": int((time.perf_counter()-t0)*1000)}))


@cli.command()
@click.option("--scheme", type=click.Choice(["cvc", "acc"]), required=True)
@click.option("--store", type=click.Path(), required=True)
@click.option("--index", type=int, required=True)
@click.option("--data", type=str, required=True)
@click.option("--proof", type=str, required=True)
def verify(scheme: str, store: str, index: int, data: str, proof: str) -> None:
    t0 = time.perf_counter()
    buf = _read_data_arg(data)
    payload = Path(proof).read_bytes()
    path = Path(store)
    if scheme == "acc":
        vds, mem, pub, st, state = _restore_acc(path)
        pr = QueryProof(scheme="acc", index=index, payload=payload)
        ok = vds.verify(pub, index, buf, pr)
    else:
        vds, mem, state = _restore_cvc(path)
        st_proxy = type("_ST", (), {})()
        from ..common.types import CVCParamsPK, CVCParamsSK
        st_proxy.pk = CVCParamsPK(**state["client_state"]["pk"])  # type: ignore[arg-type]
        st_proxy.sk = CVCParamsSK(**state["client_state"]["sk"])  # type: ignore[arg-type]
        st_proxy.root = RootDigest(**state["client_state"]["root"])  # type: ignore[arg-type]
        pr = QueryProof(scheme="cvc", index=index, payload=payload)
        ok = vds.verify(st_proxy, index, buf, pr)
    click.echo(json.dumps({"ok": bool(ok), "ms": int((time.perf_counter()-t0)*1000)}))


@cli.command()
@click.option("--scheme", type=click.Choice(["cvc", "acc"]), required=True)
@click.option("--store", type=click.Path(), required=True)
@click.option("--index", type=int, required=True)
@click.option("--data", type=str, required=True)
def update(scheme: str, store: str, index: int, data: str) -> None:
    t0 = time.perf_counter()
    path = Path(store)
    buf = _read_data_arg(data)
    if scheme == "acc":
        vds, mem, pub, st, state = _restore_acc(path)
        rec = vds.update(st, index, buf)
        state["pub"]["accumulator"] = rec.root.value
        _save_state(path, state)
        click.echo(json.dumps({"ok": True, "root": len(rec.root.value), "ms": int((time.perf_counter()-t0)*1000)}))
    else:
        vds, mem, state = _restore_cvc(path)
        st_proxy = type("_ST", (), {})()
        from ..common.types import CVCParamsPK, CVCParamsSK
        st_proxy.pk = CVCParamsPK(**state["client_state"]["pk"])  # type: ignore[arg-type]
        st_proxy.sk = CVCParamsSK(**state["client_state"]["sk"])  # type: ignore[arg-type]
        st_proxy.root = RootDigest(**state["client_state"]["root"])  # type: ignore[arg-type]
        st_proxy.cnt = int(state["client_state"]["cnt"])  # type: ignore[index]
        rec = vds.update(st_proxy, index, buf)
        state["client_state"]["root"] = st_proxy.root.model_dump()
        _save_state(path, state)
        click.echo(json.dumps({"ok": True, "root": len(rec.root.value), "ms": int((time.perf_counter()-t0)*1000)}))


if __name__ == "__main__":
    cli()
