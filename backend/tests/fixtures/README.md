# Independent Rust contract fixtures

`rust-contract.json` was captured from the Python/libSBML implementation at application revision `1c8488f74c9e5151f78489ad3bc519c8290ca042` before its removal. The embedded provenance records library versions and source SHA256 values.

The fixture contains 35 complete wire reports, their validation results, 14 ODE downloads covering all seven formats, and metadata for 106 examples. Reports use the actual Pydantic wire serializer, including its treatment of non-finite values. Tests verify source identities and compare every stable field. Request identities and elapsed times are the only normalized fields.

Do not regenerate expected results from the Rust implementation under test. New semantic cases belong in the shared Rust workspace with independently established expectations. These application fixtures protect the public contract during transport and packaging changes.
