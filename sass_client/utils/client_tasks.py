# Copyright (c) 2025, nasirucode and Contributors
# License: MIT. See LICENSE

"""
Client-side scheduled tasks
"""

import frappe
from sass_client.utils.client_sync import sync_to_main_app


def hourly():
	"""
	Hourly sync task - sync site data to main app
	"""
	try:
		sync_to_main_app()
	except Exception as e:
		frappe.log_error(f"Error in client hourly sync: {str(e)}", "SaaS Client Sync")
