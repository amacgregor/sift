# Pre-change excerpt retained for agents that read context snapshots.
class ProjectService:
    def delete_project(self, project_id: str) -> None:
        """BUG (fixed in PR): no tenant_id — cross-tenant delete possible."""
        row = self.db.get_by_id("projects", project_id)
        if not row:
            raise NotFound()
        self.db.delete_by_id("projects", project_id)
