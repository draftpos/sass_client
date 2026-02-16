import frappe
from frappe.model.document import Document
from frappe.utils import getdate, formatdate, get_url, today
from datetime import date, datetime

# --- Helper functions ---
def convert_date_to_string(date_value):
    if not date_value:
        return None
    try:
        if isinstance(date_value, str):
            parsed = getdate(date_value)
            return formatdate(parsed, "yyyy-mm-dd")
        elif isinstance(date_value, (date, datetime)):
            return formatdate(date_value, "yyyy-mm-dd")
        else:
            parsed = getdate(str(date_value))
            return formatdate(parsed, "yyyy-mm-dd")
    except Exception:
        return None

def get_subscription_info():
    site_config = frappe.conf
    package = site_config.get("subscription_package")
    status = "Active" if site_config.get("subscription_active", False) else "Expired"
    start_date = convert_date_to_string(site_config.get("subscription_start_date"))
    end_date = convert_date_to_string(site_config.get("subscription_end_date"))
    return {
        "subscription_package": package,
        "package_status": status,
        "subscription_start_date": start_date,
        "subscription_end_date": end_date
    }

def get_basic_site_info():
    site_config = frappe.conf
    companies = frappe.get_all("Company", fields=["name"])
    company_name = companies[0].name if companies else None
    client_type = site_config.get("client_type", "ERP")

    ip_address = "Unknown"
    try:
        if hasattr(frappe.local, "request") and frappe.local.request:
            ip_address = (
                frappe.get_request_header("X-Forwarded-For") or
                frappe.get_request_header("X-Real-IP") or
                getattr(frappe.local.request, "remote_addr", "Unknown")
            )
    except Exception:
        pass

    return {
        "company": company_name,
        "client_type": client_type,
        "total_companies": len(companies),
        "ip_address": ip_address,
        "site_url": get_url()
    }

def get_transaction_counts(date_filter=None):
    filters = {"docstatus": 1}
    if date_filter:
        filters["posting_date"] = ["<=", date_filter]

    sales_amount = frappe.db.get_all("Sales Invoice", filters=filters, fields=["sum(base_grand_total) as total"])
    purchase_amount = frappe.db.get_all("Purchase Invoice", filters=filters, fields=["sum(base_grand_total) as total"])

    return {
        "total_sales_invoices": frappe.db.count("Sales Invoice", filters),
        "total_credit_notes": frappe.db.count("Sales Invoice", {**filters, "is_return": 1}),
        "total_sales_invoices_amount": sales_amount[0].total or 0,
        "total_purchase_invoices": frappe.db.count("Purchase Invoice", filters),
        "total_purchase_invoice_value": purchase_amount[0].total or 0,
        "total_stock_reconciliations": frappe.db.count("Stock Reconciliation", {"docstatus": 1}),
        "active_users": frappe.db.count("User", {"enabled": 1, "name": ["!=", "Guest"]})
    }

def get_site_data(date_filter=None):
    data = {}
    data.update(get_basic_site_info())
    data.update(get_transaction_counts(date_filter))
    data.update(get_subscription_info())
    return data

# --- DocType ---
class ClientDetails(Document):
    def before_save(self):
        self.calculate_totals()

    def calculate_totals(self):
        # 1. Parse the date filter if set
        date_filter = getdate(self.date_filter) if self.date_filter else None
        # 2. Determine the filter for invoices
        filters = {"docstatus": 1}
        if date_filter:
            if self.filter_type == "On Day":
                filters["posting_date"] = date_filter
            elif self.filter_type == "Up To Date":
                filters["posting_date"] = ["<=", date_filter]

        # 3. Sales Invoices Count & Amount
        sales_amount = frappe.db.get_all("Sales Invoice", filters=filters, fields=["sum(base_grand_total) as total"])
        self.total_sales_invoices_count = frappe.db.count("Sales Invoice", filters)
        self.total_sales_invoices_amount = sales_amount[0].total or 0

        # 4. Purchase Invoices Count & Amount
        purchase_amount = frappe.db.get_all("Purchase Invoice", filters=filters, fields=["sum(base_grand_total) as total"])
        self.total_purchases_count = frappe.db.count("Purchase Invoice", filters)
        self.total_purchase_invoice_value = purchase_amount[0].total or 0

        # 5. Profit
        self.sales = self.total_sales_invoices_amount
        self.expenses = self.total_purchase_invoice_value
        self.net_profit = self.sales - self.expenses

        # 6. Stock
        self.stock_reconciliations = frappe.db.count("Stock Reconciliation", {"docstatus": 1})
        self.stock_entries_with_transfers = frappe.db.count("Stock Entry", {"purpose": "Material Transfer", "docstatus": 1})

        # 7. Active Users, Cost Centers, Warehouses
        self.total_active_users_connected_within_one_day = frappe.db.count("User", {"enabled": 1, "last_login": [">=", today()]})
        self.total_active_cost_centers = frappe.db.count("Cost Center", {"disabled": 0})
        self.total_active_warehouses = frappe.db.count("Warehouse", {"disabled": 0})

        # 8. Any transaction today
        self.any_transaction_today = "Yes" if (
            frappe.db.count("Sales Invoice", {"posting_date": today()}) or
            frappe.db.count("Purchase Invoice", {"posting_date": today()}) or
            frappe.db.count("Stock Entry", {"posting_date": today()})
        ) else "No"

        # 9. Site Info
        site_data = get_site_data(date_filter if self.filter_type == "Up To Date" else None)
        self.url = site_data["site_url"]
        self.server_ip = site_data["ip_address"]
        self.site_name = frappe.conf.get("site_name") or frappe.local.site or "ERPNext Site"
        self.default_company = site_data["company"]
