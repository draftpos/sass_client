import frappe
from frappe import _
from frappe.utils import get_url
import requests
import json
import frappe
from frappe.utils import today


def get_ip():
	response = requests.get("https://api.ipify.org?format=json").json()
	print("Public IP:", response["ip"])
	return response["ip"]



def get_site_data():
	"""
	Collect all site data to be synced to main SaaS manager
	Returns:
		dict: Site data dictionary
	"""
	try:
		# Get site configuration
		site_config = frappe.conf
		# main_app_url ="https://pay.havano.cloud"
		main_app_url = "http://127.0.0.1:8003/"
		api_key = ""

		if not main_app_url:
			frappe.log_error("SaaS Manager URL not configured", "SaaS Sync Error")
			return None

		# Get company information
		companies = frappe.get_all("Company", fields=["name"])
		company_name = companies[0].name if companies else None

		# Get client type
		client_type = site_config.get("client_type", "ERP")

		# Get IP address
		ip_address = "Unknown"
		try:
			if hasattr(frappe.local, "request") and frappe.local.request:
				ip_address = (
					frappe.get_request_header("X-Forwarded-For")
					or frappe.get_request_header("X-Real-IP")
					or getattr(frappe.local.request, "remote_addr", "Unknown")
				)
		except (AttributeError, TypeError):
			pass

		# Get site URL
		site_url = get_url()

		# Count transactions
		total_sales_invoices = frappe.db.count("Sales Invoice", {"docstatus": 1})
		total_credit_notes = frappe.db.count(
			"Sales Invoice", {"docstatus": 1, "is_return": 1}
		)
		total_purchase_invoices = frappe.db.count("Purchase Invoice", {"docstatus": 1})
		total_stock_reconciliations = frappe.db.count(
			"Stock Reconciliation", {"docstatus": 1}
		)
		# Calculate days left for subscription
		client_profile = frappe.get_single("Client Profile")

		# Grab the already calculated field
		days_left = client_profile.days_left
		print(f"Days left in subscription: {days_left}")

		# Count active users today
		active_users_today = frappe.db.count(
			"Login Tracker", {"login_time": today()}
		)

		total_companies = len(companies)

		# Subscription info
		subscription_package = site_config.get("subscription_package")
		package_status = (
			"Active" if site_config.get("subscription_active", False) else "Expired"
		)

		# Date helper
		from frappe.utils import formatdate, getdate
		from datetime import date, datetime

		def convert_date_to_string(date_value):
			if not date_value:
				return None
			try:
				if isinstance(date_value, str):
					parsed_date = getdate(date_value)
				elif isinstance(date_value, (date, datetime)):
					parsed_date = date_value
				else:
					parsed_date = getdate(str(date_value))

				return formatdate(parsed_date, "yyyy-mm-dd")
			except (ValueError, TypeError):
				return None

		# ✅ SINGLE DOCTYPE (correct place + indentation)
		client_profile = frappe.get_single("Client Profile")

		subscription_start_date = convert_date_to_string(
			client_profile.subscription_start_date
		)
		subscription_end_date = convert_date_to_string(
			client_profile.subscription_end_date
		)
		client_doc = frappe.get_all(
		"Client Details",
		fields=["assigned"],
		order_by="creation asc",
		limit_page_length=1
		)

		# Grab the boolean, default to False if no document
		assigned = client_doc[0].assigned if client_doc else False
		print(f"Assigned value: {assigned}")


		return {
			"company": company_name,
			"client_type": client_type,
			"total_sales_invoices": total_sales_invoices,
			"total_credit_notes": total_credit_notes,
			"total_purchase_invoices": total_purchase_invoices,
			"total_stock_reconciliations": total_stock_reconciliations,
			"active_users": frappe.db.count(
				"User", {"enabled": 1, "last_login": [">=", today()]}
			),
			"total_companies": total_companies,
			"ip_address": get_ip(),
			"site_url": site_url,
			"subscription_package": subscription_package,
			"package_status": package_status,
			"subscription_start_date": subscription_start_date,
			"subscription_end_date": subscription_end_date,
			"days_left": days_left,
			"assigned":assigned
		}

	except Exception as e:
		frappe.log_error(
			f"Error collecting site data: {str(e)}", "SaaS Sync Error"
		)
		return None


import frappe
from frappe import _

def block_if_subscription_expired(login_manager=None):
    # Use login_manager.user if available, otherwise fallback
    user = login_manager.user if login_manager else frappe.session.user

    if user in ("Administrator", "Guest"):
        return

    client_profile = frappe.get_single("Client Profile")
    if getattr(client_profile, "days_left", 0) <= 0:
        # This will stop the session from being created
        frappe.throw(_("Your subscription has expired. Please contact support to renew."), title=_("Subscription Expired"))

def enqueue_sync_to_main_app(login_manager):
	frappe.msgprint("on_login hook fired, starting SaaS  bri...")
	frappe.enqueue(
		"sass_client.utils.client_sync.sync_to_main_app",
		queue="short",
		timeout=300
	)

def sync_to_main_app():
	"""
	Sync site data to main SaaS manager app
	This should be called periodically via scheduled job
	"""
	try:
		site_config = frappe.conf
		# main_app_url = "https://pay.havano.cloud/"
		main_app_url = "http://127.0.0.1:8003/"
		api_key = ""
		
		if not main_app_url:
			frappe.log_error("SaaS Manager URL not configured", "SaaS Sync Error")
			return
		
		if not api_key:
			# Try to register first if no API key
			frappe.logger().info("No API key found, attempting to register site...")
			companies = frappe.get_all("Company", fields=["name"])
			company_name = companies[0].name if companies else None
			client_type = site_config.get("client_type", "ERP")
			# Get site name from site config or use site name from frappe.local
			site_name = site_config.get("site_name") or frappe.local.site or "ERPNext Site"
			
			api_key = register_client_site(site_name, company_name, client_type)
			if not api_key:
				frappe.log_error("Failed to register site and no API key available", "SaaS Sync Error")
				return
		
		# Get site data
		data = get_site_data()
		if not data:
			return
		
		# Prepare API endpoint
		api_endpoint = f"{main_app_url}/api/method/sass_manager.sass_manager.api.site_api.sync_site_data"
		
		# Make API call with proper headers (use data parameter to avoid 417 error)
		headers = {
			"Content-Type": "application/json",
		}
		payload = {
			"api_key": api_key,
			"data": data
		}
		response = requests.post(
			api_endpoint,
			data=json.dumps(payload),
			headers=headers,
			timeout=30
		)
		
		if response.status_code == 200:
			result = response.json()
			if result.get("message", {}).get("status") == "success":
				frappe.logger().info("SaaS sync successful: %s", result.get("message", {}).get("sync_id"))
			else:
				frappe.log_error("SaaS Sync Error", f"SaaS sync failed: {result.get('message', {}).get('message')}")
		else:
			frappe.log_error("SaaS Sync Error", f"SaaS sync HTTP error: {response.text}")
			
	except Exception as e:
		frappe.log_error(f"Error syncing to main app: {str(e)}", "SaaS Sync Error")


def check_user_limit():
	"""
	Check if current active users exceed subscription limit
	This should be called when creating/activating users
	"""
	try:
		site_config = frappe.conf
		main_app_url = "https://pay.havano.cloud/"
		api_key = ""
		
		if not api_key:
			# If not configured, allow unlimited users
			return True
		
		# Get subscription status
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
				max_users = package_details.get("max_users", 0)
				
				if max_users > 0:
					# Count current active users
					active_users = frappe.db.count("User", {"enabled": 1, "name": ["!=", "Guest"]})
					
					if active_users >= max_users:
						frappe.throw(_("User limit reached. Maximum {0} users allowed for your subscription package.").format(max_users))
		
		return True
	except Exception as e:
		frappe.log_error(f"Error checking user limit: {str(e)}", "SaaS User Limit Check")
		# On error, allow user creation to avoid blocking operations
		return True


def register_client_site(site_name, company=None, client_type="ERP"):
	"""
	Register this client site with main SaaS manager
	Should be called during app installation or setup
	"""
	try:
		site_config = frappe.conf
		# main_app_url = "https://pay.havano.cloud/"
		main_app_url = "http://127.0.0.1:8003/"
		
		if not main_app_url:
			frappe.log_error("SaaS Manager URL not configured", "SaaS Registration Error")
			return None
		
		site_url = get_url()
		# Get IP address safely
		ip_address = "Unknown"
		try:
			if hasattr(frappe.local, 'request') and frappe.local.request:
				ip_address = (
					frappe.get_request_header("X-Forwarded-For") or 
					frappe.get_request_header("X-Real-IP") or 
					getattr(frappe.local.request, 'remote_addr', "Unknown")
				)
		except (AttributeError, TypeError):
			# If request object is not available, use default
			pass
		
		# Register site
		api_endpoint = f"{main_app_url}/api/method/sass_manager.sass_manager.api.site_api.register_site"
		headers = {
			"Content-Type": "application/json",
		}
		payload = {
			"site_url": site_url,
			"site_name": site_name,
			"company": company,
			"client_type": client_type,
			"ip_address": ip_address
		}
		response = requests.post(
			api_endpoint,
			data=json.dumps(payload),
			headers=headers,
			timeout=30
		)
		
		if response.status_code == 200:
			result = response.json()
			reg_data = result.get("message", {})
			
			if reg_data.get("status") == "success":
				api_key = reg_data.get("api_key")
				# Note: API key should be manually added to site_config.json
				# as frappe.conf is not persistent
				frappe.logger().info("Site registered successfully. API Key: %s. Please add 'saas_api_key': '%s' to site_config.json", api_key, api_key)
				return api_key
			else:
				frappe.log_error(f"Registration failed: {reg_data.get('message')}", "SaaS Registration Error")
		return None
	except Exception as e:
		frappe.log_error(f"Error registering client site: {str(e)}", "SaaS Registration Error")
		return None
