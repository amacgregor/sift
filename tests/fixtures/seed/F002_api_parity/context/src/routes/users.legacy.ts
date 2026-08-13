// Frozen legacy behavior for reviewers/agents.
// Contract: listUsers returns only active users.
export async function listUsersLegacy(db: DB) {
  return db.users.findMany({
    where: { is_active: true },
    orderBy: { created_at: "desc" },
  });
}
