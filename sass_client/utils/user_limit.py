# Copyright (c) 2025, nasirucode and Contributors
# License: MIT. See LICENSE

"""
User limit enforcement utilities
This module enforces user limits based on subscription package
"""

import frappe
from frappe import _
import requests
import json


def enforce_user_limit():
	"""
	Enforce user limit when creating or enabling users
	This should be called via doc_events hook
	"""
	try:
		# Check if SaaS manager is configured
		site_config = frappe.conf
		if not site_config.get("saas_manager_url") or not site_config.get("saas_api_key"):
			# If not configured, allow unlimited users
			return
		
		from sass_client.utils.client_sync import check_user_limit
		check_user_limit()
	except Exception as e:
		frappe.log_error(f"Error enforcing user limit: {str(e)}", "SaaS User Limit")
		# On error, allow user creation to avoid blocking operations


def get_max_users():
	"""
	Get maximum users allowed for current subscription
	Returns 0 if unlimited or not configured
	"""
	try:
		site_config = frappe.conf
		main_app_url = site_config.get("saas_manager_url")
		api_key = site_config.get("saas_api_key")
		
		if not main_app_url or not api_key:
			return 0  # Unlimited
		
		import requests
		api_endpoint = f"{main_app_url}/api/method/sass_manager.sass_manager.api.site_api.get_subscription_status"
		headers = {
			"Content-Type": "application/json",
		}
		payload = {"api_key": api_key}
		response = requests.post(
			api_endpoint,
			data=json.dumps(payload),
			headers=headers,
			timeout=10
		)
		
		if response.status_code == 200:
			result = response.json()
			status_data = result.get("message", {})
			
			if status_data.get("status") == "success":
				package_details = status_data.get("package_details", {})
				return package_details.get("max_users", 0)
		
		return 0
	except Exception as e:
		frappe.log_error(f"Error getting max users: {str(e)}", "SaaS Max Users")
		return 0
