# create_payout is registered on both public_app (behind CDN) and internal_app (no CDN, cookie auth still on).
internal_app.add_url_rule('/payouts', view_func=create_payout, methods=['POST'])
