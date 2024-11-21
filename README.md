# Machine-readable versions of NIPs tables

Machine-readable versions of NIPs (Nostr Implementation Possibilities) tables.

## Files

The `json` directory has the following files:

- `nips.json` - NIPs list
- `kinds.json` - Kinds table
- `messages_to_client.json` - Messages from relay to client
- `messages_to_relay.json` - Messages from client to relay
- `tags.json` - Tags table

These have been updated for upstream commit `84aeb10d395d0b9a3379c81aacf5b1ff4d675499`.

## Generation

First, check out the [NIPS](https://github.com/nostr-protocol/nips) repository, then run the script with:
```
python3 read_nips_tables.py <path to NIPS repository>
```
