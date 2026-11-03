import unittest

from report_cache import sample_service


class ReportCacheTests(unittest.TestCase):
    def setUp(self):
        self.service = sample_service()

    def export(self, tenant="north", user="alex", summary_only=False):
        return self.service.export_fixed(tenant, "quarterly", user, summary_only)

    def test_reproduction_cross_tenant(self):
        self.service.export_vulnerable("north", "quarterly", "alex")
        leaked = self.service.export_vulnerable("south", "quarterly", "alex")
        self.assertEqual(leaked["internal_notes"], "North internal")

    def test_reproduction_revoked_user(self):
        self.service.export_vulnerable("north", "quarterly", "alex")
        self.service.reports[("north", "quarterly")].readers.remove("alex")
        self.assertEqual(
            self.service.export_vulnerable("north", "quarterly", "alex")["title"],
            "North report",
        )

    def test_authorized_analyst(self):
        self.assertEqual(self.export()["internal_notes"], "North internal")

    def test_tenant_isolation_both_warmup_orders(self):
        for first, second in [("north", "south"), ("south", "north")]:
            with self.subTest(first=first):
                self.service = sample_service()
                self.export(first)
                self.assertEqual(
                    self.export(second)["title"], f"{second.title()} report"
                )

    def test_same_tenant_different_projection(self):
        self.export()
        self.assertNotIn("internal_notes", self.export(user="sam"))

    def test_reader_warming_cache_does_not_strip_analyst_view(self):
        self.export(user="sam")
        self.assertEqual(self.export()["internal_notes"], "North internal")

    def test_role_downgrade(self):
        self.export()
        self.service.roles[("north", "alex")] = "reader"
        self.assertNotIn("internal_notes", self.export())

    def test_role_upgrade(self):
        self.export(user="sam")
        self.service.roles[("north", "sam")] = "analyst"
        self.assertIn("internal_notes", self.export(user="sam"))

    def test_acl_revocation_after_cache_warmup(self):
        self.export()
        self.service.reports[("north", "quarterly")].readers.remove("alex")
        with self.assertRaises(PermissionError):
            self.export()

    def test_role_removal_after_cache_warmup(self):
        self.export()
        del self.service.roles[("north", "alex")]
        with self.assertRaises(PermissionError):
            self.export()

    def test_unknown_user_cannot_consume_cached_report(self):
        self.export()
        with self.assertRaises(PermissionError):
            self.export(user="unknown")

    def test_missing_report_cannot_consume_cached_report(self):
        self.export()
        del self.service.reports[("north", "quarterly")]
        with self.assertRaises(PermissionError):
            self.export()

    def test_updated_document_version(self):
        self.export()
        report = self.service.reports[("north", "quarterly")]
        report.title = "Revised title"
        report.version += 1
        self.assertEqual(self.export()["title"], "Revised title")

    def test_summary_mode_isolated(self):
        self.export()
        self.assertNotIn("internal_notes", self.export(summary_only=True))

    def test_cache_reused_for_equal_authorized_views(self):
        self.export(user="sam")
        self.service.roles[("north", "alex")] = "reader"
        self.export()
        self.assertEqual(self.service.renders, 1)

    def test_repeated_request_reuses_cache(self):
        self.assertEqual(self.export(), self.export())
        self.assertEqual(self.service.renders, 1)

    def test_returned_dictionary_cannot_poison_cache(self):
        result = self.export()
        result["title"] = "Changed by caller"
        self.assertEqual(self.export()["title"], "North report")

    def test_tenant_only_patch_still_leaks_fields(self):
        # Separate tenant caches simulate adding tenant to the original key.
        tenant_partition = sample_service()
        tenant_partition.export_vulnerable("north", "quarterly", "alex")
        self.assertIn(
            "internal_notes",
            tenant_partition.export_vulnerable("north", "quarterly", "sam"),
        )

    def test_user_key_patch_still_replays_privileged_view(self):
        # This service instance is private to Alex: per-user separation still
        # doesn't recheck current authority or distinguish a changed field mask.
        self.service.export_vulnerable("north", "quarterly", "alex")
        self.service.roles[("north", "alex")] = "reader"
        self.assertIn(
            "internal_notes",
            self.service.export_vulnerable("north", "quarterly", "alex"),
        )


if __name__ == "__main__":
    unittest.main()
