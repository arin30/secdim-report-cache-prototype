"""Offline teaching prototype; synthetic reports, no network or real identities."""

from dataclasses import dataclass, field


@dataclass
class Report:
    version: int
    readers: set
    title: str
    public_summary: str
    internal_notes: str


@dataclass
class Service:
    reports: dict
    roles: dict
    cache: dict = field(default_factory=dict)
    renders: int = 0

    def authorize(self, tenant, report_id, user):
        report = self.reports.get((tenant, report_id))
        if report is None or user not in report.readers:
            raise PermissionError("Report unavailable")
        role = self.roles.get((tenant, user))
        if role not in {"reader", "analyst"}:
            raise PermissionError("Report unavailable")
        return report, role

    def render(self, report, fields):
        self.renders += 1
        return {name: getattr(report, name) for name in fields}

    def export_vulnerable(self, tenant, report_id, user, summary_only=False):
        # A report ID is local to an organization; this cache treats it as global.
        key = (report_id, summary_only)
        if key in self.cache:
            return dict(self.cache[key])
        report, role = self.authorize(tenant, report_id, user)
        fields = visible_fields(role, summary_only)
        body = self.render(report, fields)
        self.cache[key] = body
        return dict(body)

    def export_fixed(self, tenant, report_id, user, summary_only=False):
        # Authorization always uses current server state, including on cache hits.
        report, role = self.authorize(tenant, report_id, user)
        fields = visible_fields(role, summary_only)
        key = (tenant, report_id, report.version, fields)
        if key not in self.cache:
            self.cache[key] = self.render(report, fields)
        # Do not let a caller mutate the stored representation through the return value.
        return dict(self.cache[key])


def visible_fields(role, summary_only):
    fields = ("title", "public_summary")
    if role == "analyst" and not summary_only:
        fields += ("internal_notes",)
    return fields


def sample_service():
    return Service(
        reports={
            ("north", "quarterly"): Report(
                1, {"alex", "sam"}, "North report", "North summary", "North internal"
            ),
            ("south", "quarterly"): Report(
                1, {"alex"}, "South report", "South summary", "South internal"
            ),
        },
        roles={
            ("north", "alex"): "analyst",
            ("north", "sam"): "reader",
            ("south", "alex"): "reader",
        },
    )


def demo():
    service = sample_service()
    service.export_vulnerable("north", "quarterly", "alex")
    leaked = service.export_vulnerable("south", "quarterly", "alex")
    assert leaked["internal_notes"] == "North internal"
    print("REPRODUCED: authorized South reader receives cached North internal notes.")
    service = sample_service()
    service.export_fixed("north", "quarterly", "alex")
    south = service.export_fixed("south", "quarterly", "alex")
    assert south == {"title": "South report", "public_summary": "South summary"}
    service.roles[("north", "alex")] = "reader"
    assert "internal_notes" not in service.export_fixed("north", "quarterly", "alex")
    service.reports[("north", "quarterly")].readers.remove("alex")
    try:
        service.export_fixed("north", "quarterly", "alex")
    except PermissionError:
        print("CONTROL: tenant separation, role downgrade and revoked access enforced.")
    else:
        raise AssertionError("Revoked user retained cache access")


if __name__ == "__main__":
    demo()
