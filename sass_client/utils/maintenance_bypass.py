# Copyright (c) 2025, nasirucode and Contributors
# License: MIT. See LICENSE

"""
Utility to allow maintenance API to bypass maintenance mode
Note: This may not work if maintenance mode check happens before before_request hook
"""

import frappe


def bypass_maintenance_for_maintenance_api():
	"""
	Allow maintenance API endpoint to bypass maintenance mode
	This hook is called before_request to allow the maintenance API
	to be accessible even when the site is in maintenance mode
	
	Note: Frappe checks maintenance_mode in app.py before before_request hooks,
	so this may not work. The endpoint should still be accessible if allow_reads_during_maintenance
	is set in site_config.json, or maintenance mode needs to be removed manually.
	"""
	try:
		# Check if this is a request to the maintenance API
		if hasattr(frappe.local, 'request') and frappe.local.request:
			path = frappe.local.request.path
			if path and "/api/method/sass_client.api.maintenance_api.set_maintenance_mode" in path:
				# Try to allow reads during maintenance for this specific endpoint
				# This may not work if check happens before before_request
				if hasattr(frappe.local, 'conf') and frappe.local.conf:
					if frappe.local.conf.maintenance_mode:
						# Set allow_reads_during_maintenance to allow API access
						frappe.local.conf.allow_reads_during_maintenance = True
	except Exception:
		# If anything fails, just continue normally
		pass
