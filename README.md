# userop-hash-recheck

Recomputes the `userOpHash` of every UserOperation inside an ERC-4337 `handleOps` transaction from the raw calldata and checks it against the `UserOperationEvent` logs the EntryPoint emitted. It tells you whether what a bundler put on chain is exactly what the events (and any indexer built on them) claim, and it decodes why an op failed. EntryPoint v0.6, v0.7 and v0.8 are supported (v0.8 uses EIP-712 hashing, including the EIP-7702 initCode override). Only a JSON-RPC endpoint is needed; no explorer or indexer API.

## Example

Ethereum mainnet, EntryPoint v0.7, two sponsored ops:

```
$ python userop_hash_recheck.py https://ethereum-rpc.publicnode.com 0x4b3de80af5dcd9c615ffd05e0c212b0b9ebdc767a17ac637ff5ab02c7021a7cd
tx 0x4b3de80af5dcd9c615ffd05e0c212b0b9ebdc767a17ac637ff5ab02c7021a7cd
entrypoint 0x0000000071727de22e5e9d8baf0edac6f37da032 (v0.7) chainId 1 beneficiary 0x4337012eaf1f862b8dbdc6b62a01782ae01ef038
ops in calldata: 2, matched events: 2, unmatched events: 0

#0 sender 0xee1de888f50b79b58599df12d5320f40aaabe119 nonce 70 paymaster 0x777777777777aec03fd955926dbf81597e66834c
   hash 0xa2560740b9eef7de8fe0482d6983e1221f80df528923af77de3c61e96b1ffab1
   success yes  actualGasUsed 210383  actualGasCost 0.000034720 ETH (38.2% of prefund 0.000090926 ETH)
   status: match
#1 sender 0x8451dea7d9713c4b8ae61875f013b17284d6a9ea nonce 10 paymaster 0x777777777777aec03fd955926dbf81597e66834c
   hash 0x1c480e680de5289106c5f5d66b5ead098f7aeba446107a7494026ee9c71facde
   success yes  actualGasUsed 178198  actualGasCost 0.000029408 ETH (32.3% of prefund 0.000090926 ETH)
   status: match
```

A failed op with its postOp revert reason decoded (EntryPoint v0.7, mainnet):

```
$ python userop_hash_recheck.py https://ethereum-rpc.publicnode.com 0x9ef081b5206652c709a991656ab295fdecd0aa40da7ba300f2418ee43b21b02f
tx 0x9ef081b5206652c709a991656ab295fdecd0aa40da7ba300f2418ee43b21b02f
entrypoint 0x0000000071727de22e5e9d8baf0edac6f37da032 (v0.7) chainId 1 beneficiary 0xe469ee44d92bb173b7edc576ebb09da55dbfe32e
ops in calldata: 1, matched events: 1, unmatched events: 0

#0 sender 0x5a1b2ff924f313f9ece82d5df323e3a34b1d9365 nonce 18446744073709551623 paymaster 0x2cc0c7981d846b9f2a16276556f6e8cb52bfb633
   hash 0x911873390e23c1739ee97c1ab68c736e48e300aa7c7989a209206b4c6300ebe8
   success NO  actualGasUsed 325007  actualGasCost 0.000027158 ETH (51.6% of prefund 0.000052633 ETH)
   postOp revert: PostOpReverted(Error("Paymaster: postOp token transfer failed"))
   status: match
```

EntryPoint v0.6 reached through a bundler wrapper contract (three embedded `handleOps` calls):

```
$ python userop_hash_recheck.py https://ethereum-rpc.publicnode.com 0x66b6735ee25827b0d89a55b052023a155cbc2acd7fbe4e0e3f0373a60ec27ce4
note: tx sent via 0xb92fe925dc43a0ecde6c8b1a2709c170ec4fff4f; 3 handleOps call(s) found inside its calldata
tx 0x66b6735ee25827b0d89a55b052023a155cbc2acd7fbe4e0e3f0373a60ec27ce4
entrypoint 0x5ff137d4b0fdcd49dca30c7cf57e578a026d2789 (v0.6) chainId 1 beneficiary 0x2d1ed3d01b669d7416c1bcfcf26d3dc7ce3dae97
ops in calldata: 3, matched events: 3, unmatched events: 0

#0 sender 0x2d1ed3d01b669d7416c1bcfcf26d3dc7ce3dae97 nonce 155930327655066839810048 paymaster -
   hash 0x33df86b8ef32c754a70f2cd3c2bb296830300d1333048c5c7da5def02b55550d
   success yes  actualGasUsed 146756  actualGasCost 0.000000000 ETH (0.0% of prefund 0.000000000 ETH)
   status: match
#1 sender 0x2d1ed3d01b669d7416c1bcfcf26d3dc7ce3dae97 nonce 155930327655066839810049 paymaster -
   hash 0xcc01eaf9e115fe3271cacdedb8e94a142bc8031de6e3b7ea6c19c210c7652055
   success yes  actualGasUsed 103056  actualGasCost 0.000000000 ETH (0.0% of prefund 0.000000000 ETH)
   status: match
#2 sender 0x2d1ed3d01b669d7416c1bcfcf26d3dc7ce3dae97 nonce 155930327655066839810050 paymaster -
   hash 0xc6a3171feca7799c3776c17a1d634971bbbea19b0a9c93c251c22aecbb8394d8
   success yes  actualGasUsed 112520  actualGasCost 0.000000000 ETH (0.0% of prefund 0.000000000 ETH)
   status: match
```

The same command works on Optimism (chainId 10) and on EntryPoint v0.8 (`0x4337084d...`), where the hash is an EIP-712 typed-data hash with domain `ERC4337` / `1`.

## Usage

```
python userop_hash_recheck.py RPC_URL TX_HASH [--version v0.6|v0.7|v0.8] [--json]
```

- `RPC_URL`: any JSON-RPC endpoint for the chain the tx is on.
- `TX_HASH`: the bundler transaction (direct `handleOps` call, or a wrapper tx that embeds one or more `handleOps` calls).
- `--version`: force a hashing scheme. By default it is picked from the EntryPoint address; for an unknown EntryPoint the tool tries v0.7 and v0.8 and keeps the one whose hashes appear in the events.
- `--json`: machine-readable output.

Exit code is 0 when every op in the calldata has a matching event and every event has a matching op, 1 when something does not line up (a failed op still counts as a match), 2 when the tx cannot be found or decoded.

## How it works

1. `eth_getTransactionByHash`, `eth_getTransactionReceipt` and `eth_chainId` are fetched.
2. The calldata is ABI-decoded as `handleOps(UserOperation[],address)` (v0.6, selector `0x1fad948c`) or `handleOps(PackedUserOperation[],address)` (v0.7/v0.8, selector `0x765e827f`). If the tx went to a wrapper contract, every embedded `handleOps` selector is tried.
3. For each op the hash is recomputed: v0.6 and v0.7 use `keccak256(abi.encode(keccak256(packedFields), entryPoint, chainId))`; v0.8 uses `keccak256("\x19\x01" || domainSeparator || keccak256(typeHash || packedFields))`. If a v0.8 op carries the `0x7702` initCode marker, the sender's EIP-7702 delegate is read with `eth_getCode` at the tx block and hashed in place of the initCode, as the EntryPoint does.
4. `UserOperationEvent` logs from the EntryPoint are matched by hash; sender, nonce, paymaster and `actualGasCost <= requiredPrefund` are cross-checked. `UserOperationRevertReason` and `PostOpRevertReason` logs are decoded (`Error(string)`, `Panic(uint256)`, `PostOpReverted(bytes)`, or the raw custom selector).

keccak-256 is implemented in the file with the round constants and rotation offsets generated from the Keccak specification.

## Tests

```
python -m unittest -v
```

Tests run offline. The fixtures are real mainnet data: a full v0.7 `handleOps` calldata and its event log, and the decoded fields of a v0.6 op and a v0.8 op whose recomputed hashes must equal the hashes in the on-chain events.
