# Copyright (c) 2025, nasirucode and Contributors
# License: MIT. See LICENSE

"""
Document event hooks for user limit enforcement
"""

import frappe
from frappe import _


def validate_user_limit(doc, method):
	"""
	Validate user limit before saving user
	"""
	try:
		# Only check if user is being enabled
		if doc.enabled:
			from sass_client.utils.user_limit import enforce_user_limit
			enforce_user_limit()
	except Exception as e:
		frappe.log_error(f"Error validating user limit: {str(e)}", "SaaS User Limit Validation")
