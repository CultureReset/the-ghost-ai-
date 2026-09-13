"""Email ingestion — the universal integration surface.

Every vendor a business uses already emails them. That inbox is a complete
picture of operations, delivered automatically, and no vendor can turn it off
without breaking their own product.

Two rules carried over from the executor, for the same reasons:

  Fingerprint before parsing. Each parser declares markers that must be present.
  If they are not, the message is recorded DRIFTED and nothing is written.
  A vendor changing their template fails loudly on one message instead of
  quietly writing wrong numbers for a week.

  Nothing is overwritten. A parsed message becomes observations with a source
  and a timestamp. Canonical values are computed from them.
"""
