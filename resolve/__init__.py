"""observation -> canonical.

The missing half of "one set of hours, every surface". Ingest writes what it
saw; the executor writes what it saw; a person types what is true. All three
land in `observation`, which is append-only and full of disagreement on
purpose. Nothing turned that into an answer, so `canonical` was a table the
whole system read and nothing ever wrote.
"""
