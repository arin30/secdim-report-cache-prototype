Hi SecDim team,

I'd like to propose a separate Python challenge about a report export cache that
accidentally preserves authority as well as data. I've included a runnable
prototype, a reference fix and 19 tests before starting any SDK work.

The service hosts reports for several tenants. Analysts can see internal notes;
readers cannot. The underlying authorization code is correct, but cache hits skip
it and the cache treats tenant-local report IDs as global. A legitimate reader
can receive another tenant's cached report or a previous analyst's internal view.

The assessment would include role downgrades and ACL revocation between requests.
Adding a tenant or user to the key alone is insufficient. A successful fix must
check current access and keep representations separate by effective field
visibility and document version. It must also preserve real cache reuse and the
full analyst view for authorized users.

The prototype runs entirely offline with synthetic data and no dependencies:

```sh
python report_cache.py
python -m unittest -v
```

The current implementation assumes sequential requests. It isn't intended as a
distributed cache or concurrency challenge. I would keep the solution and security
tests out of the learner version and build the Play SDK version only after approval.

Would this be distinct enough from your existing challenges and worth developing
for the reward program? I haven't run an independent blind difficulty evaluation,
so I don't want to claim it already meets your single-attempt criterion. If this
is too familiar or too straightforward for your current needs, please let me know
before I take it further.

Thanks,
Arin Aeruva
GitHub: arin30
