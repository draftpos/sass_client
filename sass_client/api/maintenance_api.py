# Copyright (c) 2025, nasirucode and Contributors
# License: MIT. See LICENSE

"""
API endpoints for maintenance mode management
Called by sass_manager to control client site maintenance mode
"""

import frappe
from frappe import _
import json
import os


@frappe.whitelist(allow_guest=True)
def set_maintenance_mode(api_key, maintenance_mode):
	"""
	Set maintenance mode for the client site
	Called by sass_manager when site is activated/deactivated
	
	Args:
		api_key: API key for authentication (must match saas_api_key in site_config)
		maintenance_mode: 1 to enable, 0 to disable
	
	Returns:
		dict: Status of the operation
	"""
	try:
		# Validate API key
		site_config = frappe.conf
		expected_api_key = site_config.get("saas_api_key")
		
		if not expected_api_key or api_key != expected_api_key:
			return {
				"status": "error",
				"message": "Invalid API key"
			}
		
		# Convert maintenance_mode to int if it's a string
		if isinstance(maintenance_mode, str):
			maintenance_mode = int(maintenance_mode)
		
		# Get site_config.json path
		site_path = frappe.get_site_path()
		site_config_path = os.path.join(site_path, "site_config.json")
		
		# Read current config
		config = {}
		if os.path.exists(site_config_path):
			with open(site_config_path, "r") as f:
				config = json.load(f)
		
		# Update maintenance_mode
		config["maintenance_mode"] = maintenance_mode
		
		# If enabling maintenance mode, also set allow_reads_during_maintenance
		# This allows the maintenance API to still be accessible to remove maintenance mode
		if maintenance_mode:
			config["allow_reads_during_maintenance"] = True
		# Optionally remove it when disabling maintenance mode (or leave it for future use)
		# else:
		# 	config.pop("allow_reads_during_maintenance", None)
		
		# Write back to file
		with open(site_config_path, "w") as f:
			json.dump(config, f, indent=2)
		
		# Also update System Settings in database
		system_settings = frappe.get_single("System Settings")
		if maintenance_mode:
			system_settings.enable_maintenance_mode = 1
		else:
			system_settings.enable_maintenance_mode = 0
		system_settings.save(ignore_permissions=True)
		
		frappe.logger().info(f"Maintenance mode set to {maintenance_mode} for site {frappe.local.site}")
		
		return {
			"status": "success",
			"message": f"Maintenance mode {'enabled' if maintenance_mode else 'disabled'}",
			"maintenance_mode": maintenance_mode
		}
	except Exception as e:
		frappe.log_error(f"Error setting maintenance mode: {str(e)}", "Maintenance Mode Error")
		return {
			"status": "error",
			"message": str(e)
		}
