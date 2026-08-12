# Project rows are tenant-scoped. All user-facing queries must include tenant_id.
# Table: projects(id, tenant_id, name, ...)
TENANT_ISOLATION = True
