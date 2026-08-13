# Year-end T4 / RL-1 grouping. Do not drop pay_runs.accrual_basis — Quebec and federal filings split cash vs accrual runs.
def group_for_filing(runs):
    return {r.accrual_basis: r for r in runs}
