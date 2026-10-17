import unittest

import userop_hash_recheck as m

EP_V06 = "0x5ff137d4b0fdcd49dca30c7cf57e578a026d2789"
EP_V07 = "0x0000000071727de22e5e9d8baf0edac6f37da032"
EP_V08 = "0x4337084d9e255ff0702461cf8895ce9e3b5ff108"

# Ethereum mainnet tx 0xc0f70313d267ef1d54e61ffb7b9bc976bb352fed2b2d11cf3c73e038f584de02
# (block 26165799, EntryPoint v0.7): direct handleOps with one op and its event.
V07_INPUT = (
    "0x765e827f"
    "0000000000000000000000000000000000000000000000000000000000000040"
    "0000000000000000000000007202932b3be70edf0657d5bada261d610e0d7db9"
    "0000000000000000000000000000000000000000000000000000000000000001"
    "0000000000000000000000000000000000000000000000000000000000000020"
    "00000000000000000000000004922104b860d6064c86965327691bf2bf2cdbae"
    "0000fe2a54f36ded864bef35dc3ecdb10cf4b011b50e8ad10000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000120"
    "0000000000000000000000000000000000000000000000000000000000000140"
    "0000000000000000000000000001725900000000000000000000000000007d73"
    "0000000000000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000260"
    "0000000000000000000000000000000000000000000000000000000000000280"
    "0000000000000000000000000000000000000000000000000000000000000000"
    "00000000000000000000000000000000000000000000000000000000000000e4"
    "e9ae5c5300000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000000"
    "0000004000000000000000000000000000000000000000000000000000000000"
    "00000078a0b86991c6218b36c1d19d4a2e9eb0ce3606eb480000000000000000"
    "000000000000000000000000000000000000000000000000a9059cbb00000000"
    "0000000000000000d665159e8cb882c7246db8300cca00ca354863a700000000"
    "00000000000000000000000000000000000000000000000000986f7000000000"
    "0000000000000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000041"
    "045a852aac7e63125fa89b44afad07a0de44ccb9aba300c96ae270b28f27af83"
    "2c9059a3bf3922b07298092328bc93560c78fc8bb63c9ac8e8554095c4fadbef"
    "1b00000000000000000000000000000000000000000000000000000000000000"
)
V07_HASH = "0x3412ea0ea1622bf30463d42bbd1cd82dacd25b967ca64da15b0dfda3135d6eb5"
V07_LOGS = [
    {"address": EP_V07, "topics": ["0xbb47ee3e183a558b1a2ff0874b079f3fc5478b7454eacf2bfc5af2ff5878f972"],
     "data": "0x", "logIndex": "0x247"},
    {"address": EP_V07,
     "topics": [m.hexstr(m.TOPIC_USEROP_EVENT), V07_HASH,
                "0x00000000000000000000000004922104b860d6064c86965327691bf2bf2cdbae",
                "0x0000000000000000000000000000000000000000000000000000000000000000"],
     "data": "0x0000fe2a54f36ded864bef35dc3ecdb10cf4b011b50e8ad10000000000000000"
             "0000000000000000000000000000000000000000000000000000000000000001"
             "0000000000000000000000000000000000000000000000000000000000000000"
             "0000000000000000000000000000000000000000000000000000000000012ffa",
     "logIndex": "0x249"},
]

# Ethereum mainnet tx 0x66b6735ee25827b0d89a55b052023a155cbc2acd7fbe4e0e3f0373a60ec27ce4
# (EntryPoint v0.6, sent through a wrapper contract), third op.
V06_OP = {
    "layout": "v0.6", "sender": "0x2d1ed3d01b669d7416c1bcfcf26d3dc7ce3dae97",
    "nonce": 155930327655066839810050, "initCode": b"",
    "callData": bytes.fromhex(
        "2c2abd1e00000000000000000000000000000000000000000000000000000000"
        "0000002000000000000000000000000000000000000000000000000000000000"
        "0000000100000000000000000000000000000000000000000000000000000000"
        "0000002000000000000000000000000000000000000000000000000000000000"
        "0000004429565e3b9f4d97f079bbdfa0c0596943ff631003709e9014ff795115"
        "62a7fa4bb77973dc7ea132122a46367710db20a9b950fc712b119d6644daad76"
        "ebea63c5875ca6fe000000000000000000000000000000000000000000000000"
        "00000000"),
    "callGasLimit": 150000, "verificationGasLimit": 1000000, "preVerificationGas": 0,
    "maxFeePerGas": 0, "maxPriorityFeePerGas": 0, "paymasterAndData": b"",
    "paymaster": None, "paymasterVerificationGasLimit": 0, "paymasterPostOpGasLimit": 0,
}
V06_HASH = "c6a3171feca7799c3776c17a1d634971bbbea19b0a9c93c251c22aecbb8394d8"

# Ethereum mainnet tx 0x4cdb36ba024a1edf07d50620123261f451625bdba9ce4cf26d6b2c1b92c98fd6
# (EntryPoint v0.8), fourth op.
V08_OP = {
    "layout": "packed", "sender": "0x025df0b5dba789b5838309a6b149b44b629b27a6",
    "nonce": 33050671490163508402012230254592, "initCode": b"",
    "callData": bytes.fromhex(
        "b61d27f6000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead908"
        "3c756cc2000000000000000000000000000000000000000000000000000aa87b"
        "ee53800000000000000000000000000000000000000000000000000000000000"
        "0000006000000000000000000000000000000000000000000000000000000000"
        "00000004d0e30db0000000000000000000000000000000000000000000000000"
        "00000000"),
    "accountGasLimits": bytes.fromhex("0000000000000000000000000003d0900000000000000000000000000000a48c"),
    "gasFees": bytes(32), "preVerificationGas": 0, "paymasterAndData": b"",
    "verificationGasLimit": 250000, "callGasLimit": 42124, "maxFeePerGas": 0, "maxPriorityFeePerGas": 0,
    "paymaster": None, "paymasterVerificationGasLimit": 0, "paymasterPostOpGasLimit": 0,
}
V08_HASH = "2f9fc7b7caa0f632dd859d3a579429bb805a4e82dfd16e1af9cff6021cb8100f"


class KeccakTest(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(m.keccak256(b"").hex(),
                         "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470")

    def test_round_constants_and_rotations(self):
        self.assertEqual(m._RC[0], 1)
        self.assertEqual(m._RC[23], 0x8000000080008008)
        self.assertEqual(sorted(m._ROT), sorted([0, 1, 62, 28, 27, 36, 44, 6, 55, 20, 3, 10, 43, 25, 39,
                                                 41, 45, 15, 21, 8, 18, 2, 61, 56, 14]))

    def test_known_selectors_and_topics(self):
        self.assertEqual(m.SEL_HANDLEOPS_V06.hex(), "1fad948c")
        self.assertEqual(m.SEL_HANDLEOPS_PACKED.hex(), "765e827f")
        self.assertEqual(m.TOPIC_USEROP_EVENT.hex(),
                         "49628fd1471006c1482da88028e9ce4dbb080b815c9b0344d39e5a8e6ec1419f")
        self.assertEqual(m.keccak256(b"PostOpReverted(bytes)")[:4].hex(), "ad7954bc")


class HashTest(unittest.TestCase):
    def test_v06_matches_chain(self):
        self.assertEqual(m.hash_v06(V06_OP, EP_V06, 1).hex(), V06_HASH)

    def test_v08_matches_chain(self):
        self.assertEqual(m.hash_v08(V08_OP, EP_V08, 1).hex(), V08_HASH)
        self.assertEqual(m.compute_hash(V08_OP, "v0.8", EP_V08, 1).hex(), V08_HASH)

    def test_v08_scheme_differs_from_v07(self):
        self.assertNotEqual(m.hash_v07(V08_OP, EP_V08, 1).hex(), V08_HASH)

    def test_chain_id_changes_hash(self):
        self.assertNotEqual(m.hash_v06(V06_OP, EP_V06, 10).hex(), V06_HASH)

    def test_eip7702_init_code(self):
        self.assertTrue(m.is_eip7702_init_code(bytes.fromhex("7702")))
        self.assertTrue(m.is_eip7702_init_code(bytes.fromhex("7702") + bytes(18) + b"\x01\x02"))
        self.assertFalse(m.is_eip7702_init_code(bytes.fromhex("7702") + b"\x01"))
        self.assertFalse(m.is_eip7702_init_code(b""))
        delegate = "0x" + "ab" * 20
        self.assertEqual(m.eip7702_init_code_hash(bytes.fromhex("7702"), delegate),
                         m.keccak256(bytes.fromhex("ab" * 20)))
        self.assertEqual(m.eip7702_init_code_hash(bytes.fromhex("7702") + bytes(18) + b"\x01", delegate),
                         m.keccak256(bytes.fromhex("ab" * 20) + b"\x01"))
        op = dict(V08_OP, initCode=bytes.fromhex("7702"))
        with self.assertRaises(ValueError):
            m.hash_v08(op, EP_V08, 1)
        self.assertEqual(len(m.hash_v08(op, EP_V08, 1, delegate)), 32)

    def test_delegate_from_code(self):
        self.assertEqual(m.delegate_from_code(bytes.fromhex("ef0100") + bytes.fromhex("11" * 20)), "0x" + "11" * 20)
        self.assertIsNone(m.delegate_from_code(b"\x60\x80"))


class CalldataTest(unittest.TestCase):
    def test_fixture_intact(self):
        self.assertEqual(len(V07_INPUT), 1802)

    def test_parse_direct_handle_ops(self):
        calls = m.find_handle_ops(m.unhex(V07_INPUT))
        self.assertEqual(len(calls), 1)
        layout, ops, beneficiary, offset = calls[0]
        self.assertEqual((layout, offset, len(ops)), ("packed", 0, 1))
        self.assertEqual(beneficiary, "0x7202932b3be70edf0657d5bada261d610e0d7db9")
        op = ops[0]
        self.assertEqual(op["sender"], "0x04922104b860d6064c86965327691bf2bf2cdbae")
        self.assertEqual(op["verificationGasLimit"], 0x17259)
        self.assertEqual(op["callGasLimit"], 0x7d73)
        self.assertEqual(len(op["callData"]), 0xe4)
        self.assertEqual(len(op["signature"]), 65)
        self.assertIsNone(op["paymaster"])
        self.assertEqual(m.hash_v07(op, EP_V07, 1), m.unhex(V07_HASH))

    def test_embedded_handle_ops(self):
        wrapped = bytes.fromhex("cd6e13f7") + bytes(64) + m.unhex(V07_INPUT)
        calls = m.find_handle_ops(wrapped)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][3], 68)
        self.assertEqual(calls[0][1][0]["sender"], "0x04922104b860d6064c86965327691bf2bf2cdbae")

    def test_no_handle_ops(self):
        with self.assertRaises(ValueError):
            m.find_handle_ops(bytes.fromhex("a9059cbb") + bytes(64))

    def test_packed_paymaster_fields(self):
        pm = bytes.fromhex("77" * 20) + (60000).to_bytes(16, "big") + (125000).to_bytes(16, "big") + b"\x01"
        op = m.op_from_packed(["0x" + "aa" * 20, 70, b"", b"", bytes(32), 57215, bytes(32), pm, b""])
        self.assertEqual(op["paymaster"], "0x" + "77" * 20)
        self.assertEqual(op["paymasterVerificationGasLimit"], 60000)
        self.assertEqual(op["paymasterPostOpGasLimit"], 125000)

    def test_required_prefund_matches_chain_op(self):
        # mainnet tx 0x4b3de80a..., op #0: gas limits 81360/74351/60000/125000/57215 at 228500460 wei
        op = {"verificationGasLimit": 81360, "callGasLimit": 74351, "paymasterVerificationGasLimit": 60000,
              "paymasterPostOpGasLimit": 125000, "preVerificationGas": 57215, "maxFeePerGas": 228500460}
        self.assertEqual(m.required_prefund(op), 90926274045960)


class LogsAndRecheckTest(unittest.TestCase):
    def test_parse_logs(self):
        events, reverts = m.parse_logs(V07_LOGS, EP_V07)
        self.assertEqual(len(events), 1)
        ev = events[0]
        self.assertEqual(ev["userOpHash"], m.unhex(V07_HASH))
        self.assertEqual(ev["sender"], "0x04922104b860d6064c86965327691bf2bf2cdbae")
        self.assertTrue(ev["success"])
        self.assertEqual(ev["actualGasCost"], 0)
        self.assertEqual(ev["actualGasUsed"], 77818)
        self.assertEqual(reverts, {})

    def test_recheck_match(self):
        _, ops, _, _ = m.find_handle_ops(m.unhex(V07_INPUT))[0]
        events, reverts = m.parse_logs(V07_LOGS, EP_V07)
        rows, unmatched = m.recheck(ops, events, reverts, "v0.7", EP_V07, 1)
        self.assertEqual(rows[0]["status"], "match")
        self.assertEqual(unmatched, [])

    def test_recheck_detects_tampered_calldata(self):
        _, ops, _, _ = m.find_handle_ops(m.unhex(V07_INPUT))[0]
        ops[0]["nonce"] += 1
        events, reverts = m.parse_logs(V07_LOGS, EP_V07)
        rows, unmatched = m.recheck(ops, events, reverts, "v0.7", EP_V07, 1)
        self.assertIn("NO EVENT", rows[0]["status"])
        self.assertEqual(len(unmatched), 1)

    def test_recheck_wrong_chain_id(self):
        _, ops, _, _ = m.find_handle_ops(m.unhex(V07_INPUT))[0]
        events, reverts = m.parse_logs(V07_LOGS, EP_V07)
        rows, _ = m.recheck(ops, events, reverts, "v0.7", EP_V07, 10)
        self.assertIn("NO EVENT", rows[0]["status"])

    def test_detect_version(self):
        _, ops, _, _ = m.find_handle_ops(m.unhex(V07_INPUT))[0]
        events, _ = m.parse_logs(V07_LOGS, EP_V07)
        self.assertEqual(m.detect_version("packed", EP_V07, events, ops, 1), "v0.7")
        self.assertEqual(m.detect_version("packed", EP_V08, events, ops, 1), "v0.8")
        self.assertEqual(m.detect_version("v0.6", "0x" + "12" * 20, events, ops, 1), "v0.6")
        self.assertEqual(m.detect_version("packed", "0x" + "12" * 20, events, ops, 1, "v0.8"), "v0.8")
        # unknown EntryPoint address: pick the scheme whose hash appears in the events
        fake_events = [dict(events[0], userOpHash=m.hash_v08(ops[0], "0x" + "12" * 20, 1))]
        self.assertEqual(m.detect_version("packed", "0x" + "12" * 20, fake_events, ops, 1), "v0.8")

    def test_decode_revert_reason(self):
        err = m.keccak256(b"Error(string)")[:4] + (32).to_bytes(32, "big") + (3).to_bytes(32, "big") + b"abc" + bytes(29)
        self.assertEqual(m.decode_revert_reason(err), 'Error("abc")')
        panic = m.keccak256(b"Panic(uint256)")[:4] + (0x11).to_bytes(32, "big")
        self.assertEqual(m.decode_revert_reason(panic), "Panic(0x11)")
        wrapped = (m.keccak256(b"PostOpReverted(bytes)")[:4] + (32).to_bytes(32, "big")
                   + len(err).to_bytes(32, "big") + err + bytes(28))
        self.assertEqual(m.decode_revert_reason(wrapped), 'PostOpReverted(Error("abc"))')
        self.assertEqual(m.decode_revert_reason(b""), "(empty revert data)")
        self.assertTrue(m.decode_revert_reason(bytes.fromhex("deadbeef")).startswith("custom 0xdeadbeef"))

    def test_entrypoint_from_logs(self):
        self.assertEqual(m.entrypoint_from_logs(V07_LOGS, "0x" + "00" * 20), EP_V07)
        self.assertEqual(m.entrypoint_from_logs([], "0xfallback"), "0xfallback")


if __name__ == "__main__":
    unittest.main()
