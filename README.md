# Cached authority

A small, offline SecDim proposal prototype about multi-tenant report exports.
This is intentionally vulnerable educational code, not a finding in SecDim or
another product. No reward or development approval has been granted.

## Run

Python 3.11+, standard library only:

```sh
python report_cache.py
python -m unittest -v
```

The demo reproduces a South reader receiving North's cached internal notes,
then checks the reference solution against tenant separation, downgrade and
revocation. The 19 tests include legitimate cache reuse; disabling caching or
stripping every internal field is not an acceptable solution.

## Threat model

A fictional SaaS export service receives a tenant, a report identifier and an
authenticated user. Authentication and tenant selection are trusted server-side
context, not client-controlled headers. Report IDs are tenant-local. Report ACLs,
user roles and report versions live in an authoritative in-memory data store.
The attacker can make ordinary export requests using their own identity. They
cannot edit roles, ACLs or reports. The tests change these as trusted administrator
actions between requests to model normal account lifecycle events.

Two tenants may have a user with the same display identifier; membership is keyed
by tenant and user. The cache is shared by all requests. Analyst views contain
internal notes, while reader and summary views do not. All strings are synthetic.
No network, credentials, exploitation of real services or external packages.

## Defect and intended lesson

`export_vulnerable` returns a cached representation before checking current
authorization, and keys it by a tenant-local report ID and summary flag. This
allows both tenant confusion and reuse of a more privileged representation.

Merely adding the tenant doesn't isolate reader/analyst projections. Merely
adding a user doesn't handle a role downgrade or ACL revocation. Reauthorizing
but keeping a shared privileged body also leaves field leakage. Conversely,
rejecting every cache hit, disabling caching or omitting analyst fields breaks
legitimate functionality. The learner must distinguish permission to request an
object from the authority and freshness of the cached representation.

## Reference solution

`export_fixed` authorizes every request against current server state before a
cache hit can be returned. It derives the field mask from the current role and
requested view, then keys the representation by tenant, report identifier,
monotonic content version and field mask. Equivalent authorized views can share
work without sharing authority. It returns a copy of the cached dictionary.

Content version must advance on every content change. The prototype assumes
sequential requests and atomic administration updates. It makes no concurrency,
distributed invalidation, memory-bounding or production-readiness claims. A real
implementation needs coherent database snapshots and a cache lifecycle design.
These are explicitly outside this proposal's scope.

## Assessment plan and status

Target: intermediate application security, subject to review. The reviewer copy
includes both implementations and all tests. A learner copy would expose the
service and ordinary behavior tests, keeping the reference solution and security
assessment private. Full Play SDK development would follow proposal approval.

Difficulty has not been independently evaluated. This prototype does NOT
establish resistance to a general-purpose AI solving it in one attempt. SecDim
must decide whether its scope and difficulty meet their acceptance bar. This is
a different scenario from the archive proposal, but no claim of comprehensive
originality across their existing library is made.
