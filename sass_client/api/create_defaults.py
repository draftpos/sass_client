import frappe
from frappe.utils import now_datetime

def add_product_types():
    product_list = [
        "Mobile POS",
        "Desktop POS Offline",
        "Desktop POS Online + Offline Sync",
        "ERP",
        "Fiscalisation",
        "Hotel Management"
    ]

    for p in product_list:
        if not frappe.db.exists("Product Type", p):
            doc = frappe.get_doc({
                "doctype": "Product Type",
                "product": p
            })
            doc.insert(ignore_permissions=True)
            print(f"Added: {p}")
        else:
            print(f"Already exists: {p}")


import frappe
from frappe.utils import today

def track_login(login_manager):
    # Confirm the hook fires
    frappe.msgprint(f"🔥 track_login hook fired for user: {login_manager.user}")

    user = login_manager.user
    login_date = today()  # Just the date, no time

    # Check if a record for this user and date already exists
    exists = frappe.db.exists("Login Tracker", {"user": user, "login_time": login_date})

    if exists:
        print(f"Login already recorded for {user} on {login_date}, skipping...")
        return

    try:
        frappe.get_doc({
            "doctype": "Login Tracker",
            "user": user,
            "login_time": login_date
        }).insert(ignore_permissions=True)
        print(f"Login recorded for {user} on {login_date}")
    except Exception:
        frappe.log_error(frappe.get_traceback(), f"Login Tracker Error for {user}")
