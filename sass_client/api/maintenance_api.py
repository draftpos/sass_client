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
def set_maintenance_mode(api_key, maintenance_mode, allow_reads_during_maintenance=None):
	"""
	Set maintenance mode for the client site
	Called by sass_manager when site is activated/deactivated
	
	Args:
		api_key: API key for authentication (must match saas_api_key in site_config)
		maintenance_mode: 1 to enable, 0 to disable
		allow_reads_during_maintenance: True/1 to allow reads, False/0 to disallow (optional)
	
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
		
		# Handle allow_reads_during_maintenance
		# If explicitly provided, use that value; otherwise default based on maintenance_mode
		if allow_reads_during_maintenance is not None:
			# Convert to boolean/int if it's a string
			if isinstance(allow_reads_during_maintenance, str):
				allow_reads_during_maintenance = allow_reads_during_maintenance.lower() in ('true', '1', 'yes')
			allow_reads_during_maintenance = bool(allow_reads_during_maintenance)
		else:
			# Default behavior: if enabling maintenance mode, allow reads (for API access)
			# If disabling, remove the setting (or keep it if already set)
			allow_reads_during_maintenance = bool(maintenance_mode)
		
		if maintenance_mode:
			# Only set if enabling maintenance mode
			if allow_reads_during_maintenance:
				config["allow_reads_during_maintenance"] = True
			else:
				# Remove if explicitly set to False
				config.pop("allow_reads_during_maintenance", None)
		else:
			# When disabling maintenance mode, remove the setting
			config.pop("allow_reads_during_maintenance", None)
		
		# Write back to file
		with open(site_config_path, "w") as f:
			json.dump(config, f, indent=2)
		
		# Also update System Settings in database (if not in read-only mode)
		# Skip database update if site is in read-only mode during maintenance
		# try:
		# 	system_settings = frappe.get_single("System Settings")
		# 	if maintenance_mode:
		# 		system_settings.enable_maintenance_mode = 1
		# 	else:
		# 		system_settings.enable_maintenance_mode = 0
		# 	system_settings.save(ignore_permissions=True)
		# except frappe.InReadOnlyMode:
		# 	# Site is in read-only mode, skip database update
		# 	# The site_config.json update is sufficient for maintenance mode to work
		# 	frappe.logger().info(
		# 		f"Site is in read-only mode, skipping System Settings update. "
		# 		f"Maintenance mode updated in site_config.json only."
		# 	)
		# except Exception as e:
		# 	# Log other errors but don't fail the operation
		# 	# The site_config.json update is the primary method and is already done
		# 	frappe.log_error(
		# 		f"Error updating System Settings for maintenance mode: {str(e)}",
		# 		"Maintenance Mode Warning"
		# 	)
		
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
