#!/usr/bin/env python3
"""Recompute ERC-4337 userOpHash values from a handleOps transaction and
compare them with the UserOperationEvent logs the EntryPoint emitted.

Supports EntryPoint v0.6, v0.7 and v0.8 (EIP-712 hashing, including the
EIP-7702 initCode override). Only the JSON-RPC endpoint is needed.
"""

import argparse
import json
import sys
import urllib.request

USER_AGENT = "userop-hash-recheck/0.1"

ENTRYPOINTS = {
    "0x5ff137d4b0fdcd49dca30c7cf57e578a026d2789": "v0.6",
    "0x0000000071727de22e5e9d8baf0edac6f37da032": "v0.7",
    "0x4337084d9e255ff0702461cf8895ce9e3b5ff108": "v0.8",
}

# ---------------------------------------------------------------- keccak-256


def _keccak_constants():
    """Round constants via the LFSR and rotation offsets via (t+1)(t+2)/2."""

    def rc_bit(t):
        if t % 255 == 0:
            return 1
        r = 1
        for _ in range(t % 255):
            r <<= 1
            if r & 0x100:
                r ^= 0x171
        return r & 1

    round_constants = []
    for ir in range(24):
        rc = 0
        for j in range(7):
            rc |= rc_bit(j + 7 * ir) << ((1 << j) - 1)
        round_constants.append(rc)

    rotations = [0] * 25
    x, y = 1, 0
    for t in range(24):
        rotations[x + 5 * y] = ((t + 1) * (t + 2) // 2) % 64
        x, y = y, (2 * x + 3 * y) % 5
    return round_constants, rotations


_RC, _ROT = _keccak_constants()
_MASK = (1 << 64) - 1


def _keccak_f(state):
    for rnd in range(24):
        c = [state[x] ^ state[x + 5] ^ state[x + 10] ^ state[x + 15] ^ state[x + 20] for x in range(5)]
        d = [c[(x - 1) % 5] ^ (((c[(x + 1) % 5] << 1) | (c[(x + 1) % 5] >> 63)) & _MASK) for x in range(5)]
        a = [state[i] ^ d[i % 5] for i in range(25)]
        b = [0] * 25
        for x in range(5):
            for y in range(5):
                r = _ROT[x + 5 * y]
                v = a[x + 5 * y]
                b[y + 5 * ((2 * x + 3 * y) % 5)] = ((v << r) | (v >> (64 - r))) & _MASK if r else v
        for x in range(5):
            for y in range(5):
                state[x + 5 * y] = b[x + 5 * y] ^ ((~b[(x + 1) % 5 + 5 * y]) & b[(x + 2) % 5 + 5 * y])
        state[0] ^= _RC[rnd]


def keccak256(data: bytes) -> bytes:
    rate = 136
    state = [0] * 25
    padded = bytearray(data)
    padded.append(0x01)
    while len(padded) % rate:
        padded.append(0)
    padded[-1] |= 0x80
    for off in range(0, len(padded), rate):
        block = padded[off:off + rate]
        for i in range(rate // 8):
            state[i] ^= int.from_bytes(block[8 * i:8 * i + 8], "little")
        _keccak_f(state)
    out = b"".join(state[i].to_bytes(8, "little") for i in range(4))
    return out[:32]


# ------------------------------------------------------------------ ABI utils


def hexstr(b: bytes) -> str:
    return "0x" + b.hex()


def unhex(s: str) -> bytes:
    s = s[2:] if s.startswith("0x") else s
    return bytes.fromhex(s)


def word(value: int) -> bytes:
    return value.to_bytes(32, "big")


def addr_word(addr: str) -> bytes:
    return bytes(12) + unhex(addr)


def _is_dynamic(typ):
    if isinstance(typ, dict):
        return True
    if isinstance(typ, list):
        return any(_is_dynamic(t) for t in typ)
    return typ in ("bytes", "string")


def abi_decode(typ, data: bytes, pos: int = 0):
    """Minimal ABI decoder. typ: 'address'|'uint256'|'bytes32'|'bool'|'bytes',
    a list for a tuple, or {'array': elem} for a dynamic array."""
    if isinstance(typ, dict):
        length = int.from_bytes(data[pos:pos + 32], "big")
        base = pos + 32
        elem = typ["array"]
        out = []
        for i in range(length):
            if _is_dynamic(elem):
                off = int.from_bytes(data[base + 32 * i:base + 32 * i + 32], "big")
                out.append(abi_decode(elem, data, base + off))
            else:
                out.append(abi_decode(elem, data, base + 32 * i))
        return out
    if isinstance(typ, list):
        out = []
        cur = pos
        for comp in typ:
            if _is_dynamic(comp):
                off = int.from_bytes(data[cur:cur + 32], "big")
                out.append(abi_decode(comp, data, pos + off))
                cur += 32
            else:
                out.append(abi_decode(comp, data, cur))
                cur += 32
        return out
    w = data[pos:pos + 32]
    if typ == "address":
        return "0x" + w[12:].hex()
    if typ == "uint256":
        return int.from_bytes(w, "big")
    if typ == "bytes32":
        return w
    if typ == "bool":
        return int.from_bytes(w, "big") != 0
    if typ == "bytes":
        length = int.from_bytes(w, "big")
        return data[pos + 32:pos + 32 + length]
    raise ValueError("unsupported type %r" % (typ,))


USEROP_V06 = ["address", "uint256", "bytes", "bytes", "uint256", "uint256",
              "uint256", "uint256", "uint256", "bytes", "bytes"]
PACKED_USEROP = ["address", "uint256", "bytes", "bytes", "bytes32", "uint256",
                 "bytes32", "bytes", "bytes"]

SEL_HANDLEOPS_V06 = keccak256(
    b"handleOps((address,uint256,bytes,bytes,uint256,uint256,uint256,uint256,uint256,bytes,bytes)[],address)")[:4]
SEL_HANDLEOPS_PACKED = keccak256(
    b"handleOps((address,uint256,bytes,bytes,bytes32,uint256,bytes32,bytes,bytes)[],address)")[:4]

TOPIC_USEROP_EVENT = keccak256(b"UserOperationEvent(bytes32,address,address,uint256,bool,uint256,uint256)")
TOPIC_REVERT_REASON = keccak256(b"UserOperationRevertReason(bytes32,address,uint256,bytes)")
TOPIC_POSTOP_REVERT = keccak256(b"PostOpRevertReason(bytes32,address,uint256,bytes)")

PACKED_USEROP_TYPEHASH = keccak256(
    b"PackedUserOperation(address sender,uint256 nonce,bytes initCode,bytes callData,"
    b"bytes32 accountGasLimits,uint256 preVerificationGas,bytes32 gasFees,bytes paymasterAndData)")
EIP712_DOMAIN_TYPEHASH = keccak256(
    b"EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)")


# ------------------------------------------------------------ userop parsing


def parse_handle_ops(calldata: bytes):
    """Return (layout, ops, beneficiary). layout is 'v0.6' or 'packed'."""
    sel = calldata[:4]
    if sel == SEL_HANDLEOPS_V06:
        ops, beneficiary = abi_decode([{"array": USEROP_V06}, "address"], calldata, 4)
        return "v0.6", [op_from_v06(o) for o in ops], beneficiary
    if sel == SEL_HANDLEOPS_PACKED:
        ops, beneficiary = abi_decode([{"array": PACKED_USEROP}, "address"], calldata, 4)
        return "packed", [op_from_packed(o) for o in ops], beneficiary
    raise ValueError("not a handleOps call (selector %s)" % hexstr(sel))


def find_handle_ops(calldata: bytes):
    """Return a list of (layout, ops, beneficiary, offset) for every handleOps
    call in the tx input. A direct call gives one entry at offset 0; a tx that
    went through a wrapper contract may embed several handleOps calls."""
    try:
        layout, ops, beneficiary = parse_handle_ops(calldata)
        return [(layout, ops, beneficiary, 0)]
    except ValueError:
        pass
    found = []
    for sel in (SEL_HANDLEOPS_PACKED, SEL_HANDLEOPS_V06):
        start = 0
        while True:
            idx = calldata.find(sel, start)
            if idx < 0:
                break
            try:
                layout, ops, beneficiary = parse_handle_ops(calldata[idx:])
                if ops:
                    found.append((layout, ops, beneficiary, idx))
            except (ValueError, IndexError, OverflowError):
                pass
            start = idx + 1
    if not found:
        raise ValueError("no handleOps call found in transaction input")
    found.sort(key=lambda f: f[3])
    return found


def entrypoint_from_logs(logs, fallback: str) -> str:
    for lg in logs:
        if lg.get("topics") and unhex(lg["topics"][0]) == TOPIC_USEROP_EVENT:
            return lg["address"]
    return fallback


def op_from_v06(fields):
    (sender, nonce, init_code, call_data, call_gas, ver_gas, pre_ver_gas,
     max_fee, max_prio, pm_data, sig) = fields
    return {
        "layout": "v0.6", "sender": sender, "nonce": nonce,
        "initCode": init_code, "callData": call_data,
        "callGasLimit": call_gas, "verificationGasLimit": ver_gas,
        "preVerificationGas": pre_ver_gas, "maxFeePerGas": max_fee,
        "maxPriorityFeePerGas": max_prio, "paymasterAndData": pm_data,
        "signature": sig,
        "paymaster": "0x" + pm_data[:20].hex() if len(pm_data) >= 20 else None,
        "paymasterVerificationGasLimit": 0, "paymasterPostOpGasLimit": 0,
    }


def op_from_packed(fields):
    (sender, nonce, init_code, call_data, acct_gas, pre_ver_gas, gas_fees,
     pm_data, sig) = fields
    op = {
        "layout": "packed", "sender": sender, "nonce": nonce,
        "initCode": init_code, "callData": call_data,
        "accountGasLimits": acct_gas, "gasFees": gas_fees,
        "verificationGasLimit": int.from_bytes(acct_gas[:16], "big"),
        "callGasLimit": int.from_bytes(acct_gas[16:], "big"),
        "preVerificationGas": pre_ver_gas,
        "maxPriorityFeePerGas": int.from_bytes(gas_fees[:16], "big"),
        "maxFeePerGas": int.from_bytes(gas_fees[16:], "big"),
        "paymasterAndData": pm_data, "signature": sig,
        "paymaster": None, "paymasterVerificationGasLimit": 0,
        "paymasterPostOpGasLimit": 0,
    }
    if len(pm_data) >= 52:
        op["paymaster"] = "0x" + pm_data[:20].hex()
        op["paymasterVerificationGasLimit"] = int.from_bytes(pm_data[20:36], "big")
        op["paymasterPostOpGasLimit"] = int.from_bytes(pm_data[36:52], "big")
    return op


def required_prefund(op) -> int:
    """Max wei the EntryPoint may charge for the op (EntryPoint _getRequiredPrefund)."""
    gas = (op["verificationGasLimit"] + op["callGasLimit"] + op["paymasterVerificationGasLimit"]
           + op["paymasterPostOpGasLimit"] + op["preVerificationGas"])
    return gas * op["maxFeePerGas"]


# --------------------------------------------------------------- hashing


def hash_v06(op, entrypoint: str, chain_id: int) -> bytes:
    packed = b"".join([
        addr_word(op["sender"]), word(op["nonce"]),
        keccak256(op["initCode"]), keccak256(op["callData"]),
        word(op["callGasLimit"]), word(op["verificationGasLimit"]),
        word(op["preVerificationGas"]), word(op["maxFeePerGas"]),
        word(op["maxPriorityFeePerGas"]), keccak256(op["paymasterAndData"]),
    ])
    return keccak256(keccak256(packed) + addr_word(entrypoint) + word(chain_id))


def _packed_fields(op, init_code_hash: bytes) -> bytes:
    return b"".join([
        addr_word(op["sender"]), word(op["nonce"]),
        init_code_hash, keccak256(op["callData"]),
        op["accountGasLimits"], word(op["preVerificationGas"]),
        op["gasFees"], keccak256(op["paymasterAndData"]),
    ])


def hash_v07(op, entrypoint: str, chain_id: int) -> bytes:
    inner = keccak256(_packed_fields(op, keccak256(op["initCode"])))
    return keccak256(inner + addr_word(entrypoint) + word(chain_id))


def domain_separator_v08(entrypoint: str, chain_id: int) -> bytes:
    return keccak256(EIP712_DOMAIN_TYPEHASH + keccak256(b"ERC4337") + keccak256(b"1")
                     + word(chain_id) + addr_word(entrypoint))


def is_eip7702_init_code(init_code: bytes) -> bool:
    """EntryPoint v0.8 marker: the first 20 bytes (zero padded) are 0x7702."""
    if len(init_code) < 2:
        return False
    head = (init_code[:20] + bytes(20))[:20]
    return head == b"\x77\x02" + bytes(18)


def eip7702_init_code_hash(init_code: bytes, delegate: str) -> bytes:
    """v0.8 override: hash of the sender's 7702 delegate plus any init calldata."""
    tail = init_code[20:] if len(init_code) > 20 else b""
    return keccak256(unhex(delegate) + tail)


def hash_v08(op, entrypoint: str, chain_id: int, delegate: str = None) -> bytes:
    if is_eip7702_init_code(op["initCode"]):
        if delegate is None:
            raise ValueError("EIP-7702 initCode needs the sender's delegate address")
        init_hash = eip7702_init_code_hash(op["initCode"], delegate)
    else:
        init_hash = keccak256(op["initCode"])
    struct_hash = keccak256(PACKED_USEROP_TYPEHASH + _packed_fields(op, init_hash))
    return keccak256(b"\x19\x01" + domain_separator_v08(entrypoint, chain_id) + struct_hash)


def compute_hash(op, version: str, entrypoint: str, chain_id: int, delegate: str = None) -> bytes:
    if version == "v0.6":
        return hash_v06(op, entrypoint, chain_id)
    if version == "v0.7":
        return hash_v07(op, entrypoint, chain_id)
    if version == "v0.8":
        return hash_v08(op, entrypoint, chain_id, delegate)
    raise ValueError("unknown version " + version)


def delegate_from_code(code: bytes):
    """EIP-7702 delegation designator: 0xef0100 || 20-byte address."""
    if len(code) == 23 and code[:3] == b"\xef\x01\x00":
        return "0x" + code[3:].hex()
    return None


# ------------------------------------------------------------ log decoding


def decode_revert_reason(data: bytes) -> str:
    if len(data) == 0:
        return "(empty revert data)"
    sel = data[:4]
    if sel == keccak256(b"Error(string)")[:4] and len(data) >= 68:
        off = int.from_bytes(data[4:36], "big")
        ln = int.from_bytes(data[4 + off:4 + off + 32], "big")
        return "Error(%s)" % json.dumps(data[36 + off:36 + off + ln].decode("utf-8", "replace"))
    if sel == keccak256(b"Panic(uint256)")[:4] and len(data) >= 36:
        return "Panic(0x%x)" % int.from_bytes(data[4:36], "big")
    if sel == keccak256(b"PostOpReverted(bytes)")[:4] and len(data) >= 68:
        inner = abi_decode(["bytes"], data[4:])[0]
        return "PostOpReverted(%s)" % decode_revert_reason(inner)
    return "custom %s (%d bytes)" % (hexstr(sel), len(data))


def parse_logs(logs, entrypoint: str):
    """Collect UserOperationEvent / revert-reason logs emitted by the EntryPoint."""
    events, reverts = [], {}
    for lg in logs:
        if lg["address"].lower() != entrypoint.lower() or not lg["topics"]:
            continue
        t0 = unhex(lg["topics"][0])
        data = unhex(lg["data"])
        if t0 == TOPIC_USEROP_EVENT:
            nonce, success, cost, gas_used = abi_decode(["uint256", "bool", "uint256", "uint256"], data)
            events.append({
                "userOpHash": unhex(lg["topics"][1]),
                "sender": "0x" + lg["topics"][2][-40:],
                "paymaster": "0x" + lg["topics"][3][-40:],
                "nonce": nonce, "success": success,
                "actualGasCost": cost, "actualGasUsed": gas_used,
                "logIndex": int(lg["logIndex"], 16) if isinstance(lg.get("logIndex"), str) else lg.get("logIndex"),
            })
        elif t0 in (TOPIC_REVERT_REASON, TOPIC_POSTOP_REVERT):
            _nonce, reason = abi_decode(["uint256", "bytes"], data)
            kind = "callData revert" if t0 == TOPIC_REVERT_REASON else "postOp revert"
            reverts[unhex(lg["topics"][1])] = "%s: %s" % (kind, decode_revert_reason(reason))
    return events, reverts


# ------------------------------------------------------------- core check


def recheck(ops, events, reverts, version: str, entrypoint: str, chain_id: int, delegates=None):
    """Match calldata ops against emitted events. Returns a list of result rows."""
    delegates = delegates or {}
    by_hash = {e["userOpHash"]: e for e in events}
    rows = []
    for i, op in enumerate(ops):
        row = {"index": i, "sender": op["sender"], "nonce": op["nonce"],
               "paymaster": op["paymaster"], "prefund": required_prefund(op)}
        try:
            h = compute_hash(op, version, entrypoint, chain_id, delegates.get(op["sender"].lower()))
        except ValueError as exc:
            row.update({"computed": None, "status": "cannot hash: %s" % exc})
            rows.append(row)
            continue
        row["computed"] = h
        ev = by_hash.pop(h, None)
        if ev is None:
            row["status"] = "NO EVENT (hash mismatch or op dropped)"
        else:
            row["event"] = ev
            problems = []
            if ev["sender"].lower() != op["sender"].lower():
                problems.append("sender differs")
            if ev["nonce"] != op["nonce"]:
                problems.append("nonce differs")
            ev_pm = ev["paymaster"].lower()
            op_pm = (op["paymaster"] or "0x" + "00" * 20).lower()
            if ev_pm != op_pm:
                problems.append("paymaster differs")
            if ev["actualGasCost"] > row["prefund"]:
                problems.append("actualGasCost above prefund")
            row["status"] = "match" if not problems else "; ".join(problems)
            row["revert"] = reverts.get(h)
        rows.append(row)
    unmatched = [{"event": e, "status": "event without matching calldata op"} for e in by_hash.values()]
    return rows, unmatched


def detect_version(ops_layout: str, entrypoint: str, events, ops, chain_id: int, override: str = None):
    if override:
        return override
    known = ENTRYPOINTS.get(entrypoint.lower())
    if known:
        return known
    if ops_layout == "v0.6":
        return "v0.6"
    hashes = {e["userOpHash"] for e in events}
    for cand in ("v0.7", "v0.8"):
        for op in ops:
            try:
                if compute_hash(op, cand, entrypoint, chain_id) in hashes:
                    return cand
            except ValueError:
                continue
    return "v0.7"


# ------------------------------------------------------------------- RPC


class Rpc:
    def __init__(self, url: str):
        self.url = url
        self._id = 0

    def call(self, method: str, params):
        self._id += 1
        body = json.dumps({"jsonrpc": "2.0", "id": self._id, "method": method, "params": params}).encode()
        req = urllib.request.Request(self.url, data=body, headers={
            "Content-Type": "application/json", "User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                out = json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            raise RuntimeError("HTTP %d from RPC for %s" % (exc.code, method))
        if "error" in out:
            raise RuntimeError("RPC error %s: %s" % (method, out["error"]))
        return out["result"]


def fetch_delegates(rpc, ops, block_tag: str):
    out = {}
    for op in ops:
        if op["layout"] == "packed" and is_eip7702_init_code(op["initCode"]):
            code = unhex(rpc.call("eth_getCode", [op["sender"], block_tag]))
            d = delegate_from_code(code)
            if d:
                out[op["sender"].lower()] = d
    return out


def fmt_eth(wei: int) -> str:
    return "%.9f" % (wei / 1e18)


def format_report(tx_hash, entrypoint, version, chain_id, beneficiary, rows, unmatched):
    lines = ["tx %s" % tx_hash,
             "entrypoint %s (%s) chainId %d beneficiary %s" % (entrypoint, version, chain_id, beneficiary),
             "ops in calldata: %d, matched events: %d, unmatched events: %d" % (
                 len(rows), sum(1 for r in rows if r.get("event")), len(unmatched)), ""]
    for r in rows:
        ev = r.get("event")
        lines.append("#%d sender %s nonce %d paymaster %s" % (
            r["index"], r["sender"], r["nonce"], r["paymaster"] or "-"))
        lines.append("   hash %s" % (hexstr(r["computed"]) if r["computed"] else "-"))
        if ev:
            pct = (100.0 * ev["actualGasCost"] / r["prefund"]) if r["prefund"] else 0.0
            lines.append("   success %s  actualGasUsed %d  actualGasCost %s ETH (%.1f%% of prefund %s ETH)" % (
                "yes" if ev["success"] else "NO", ev["actualGasUsed"], fmt_eth(ev["actualGasCost"]),
                pct, fmt_eth(r["prefund"])))
            if r.get("revert"):
                lines.append("   %s" % r["revert"])
        lines.append("   status: %s" % r["status"])
    for u in unmatched:
        e = u["event"]
        lines.append("event %s sender %s nonce %d: %s" % (hexstr(e["userOpHash"]), e["sender"], e["nonce"], u["status"]))
    return "\n".join(lines)


def to_json(rows, unmatched):
    def conv(v):
        if isinstance(v, bytes):
            return hexstr(v)
        if isinstance(v, dict):
            return {k: conv(x) for k, x in v.items()}
        if isinstance(v, list):
            return [conv(x) for x in v]
        return v
    return json.dumps({"ops": conv(rows), "unmatched_events": conv(unmatched)}, indent=2)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Recompute ERC-4337 userOpHash values of a handleOps tx and compare with EntryPoint events.")
    ap.add_argument("rpc_url", help="JSON-RPC endpoint")
    ap.add_argument("tx_hash", help="hash of the bundler's handleOps transaction")
    ap.add_argument("--version", choices=["v0.6", "v0.7", "v0.8"], help="force EntryPoint hashing scheme (default: detect)")
    ap.add_argument("--json", action="store_true", help="print JSON instead of text")
    args = ap.parse_args(argv)

    rpc = Rpc(args.rpc_url)
    tx = rpc.call("eth_getTransactionByHash", [args.tx_hash])
    if tx is None:
        print("transaction not found", file=sys.stderr)
        return 2
    receipt = rpc.call("eth_getTransactionReceipt", [args.tx_hash])
    if receipt is None:
        print("transaction is not mined yet", file=sys.stderr)
        return 2
    chain_id = int(rpc.call("eth_chainId", []), 16)
    entrypoint = tx["to"]
    if entrypoint.lower() not in ENTRYPOINTS:
        entrypoint = entrypoint_from_logs(receipt["logs"], entrypoint)
    try:
        calls = find_handle_ops(unhex(tx["input"]))
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    layout = calls[0][0]
    ops = [op for c in calls for op in c[1]]
    beneficiary = ", ".join(sorted({c[2] for c in calls}))
    if calls[0][3]:
        print("note: tx sent via %s; %d handleOps call(s) found inside its calldata" % (tx["to"], len(calls)))
    events, reverts = parse_logs(receipt["logs"], entrypoint)
    version = detect_version(layout, entrypoint, events, ops, chain_id, args.version)
    delegates = {}
    if version == "v0.8":
        delegates = fetch_delegates(rpc, ops, receipt["blockNumber"])
    rows, unmatched = recheck(ops, events, reverts, version, entrypoint, chain_id, delegates)
    if args.json:
        print(to_json(rows, unmatched))
    else:
        print(format_report(args.tx_hash, entrypoint, version, chain_id, beneficiary, rows, unmatched))
    bad = [r for r in rows if r["status"] != "match"] + unmatched
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
