import frappe
@frappe.whitelist(allow_guest=True)
def create_admin_user(username=None, email=None, password=None, company=None):
    """
    Create a new admin user with full permissions and assign company
    """

    try:
        # -----------------------------
        # Mandatory checks
        # -----------------------------
        missing = []
        if not username:
            missing.append("username")
        if not email:
            missing.append("email")
        if not password:
            missing.append("password")
        if not company:
            missing.append("company")

        if missing:
            return {
                "status": "error",
                "message": f"Missing required fields: {', '.join(missing)}"
            }

        # -----------------------------
        # Create company if not exists
        # -----------------------------
        if not frappe.db.exists("Company", company):
            company_doc = frappe.get_doc({
                "doctype": "Company",
                "company_name": company,
                "default_currency": "USD"
            })
            company_doc.flags.ignore_permissions = True
            company_doc.insert()

        # -----------------------------
        # Check if user exists
        # -----------------------------
        if frappe.db.exists("User", email):
            return {
                "status": "error",
                "message": "User already exists"
            }

        # -----------------------------
        # Create user
        # -----------------------------
        user = frappe.get_doc({
            "doctype": "User",
            "email": email,
            "first_name": username,
            "enabled": 1,
            "new_password": password,
            "send_welcome_email": 0
        })

        user.flags.ignore_permissions = True
        user.insert(ignore_permissions=True)

        # -----------------------------
        # Assign full admin role
        # -----------------------------
        user.add_roles("System Manager")

        # -----------------------------
        # Set company permission
        # -----------------------------
        if not frappe.db.exists(
            "User Permission",
            {
                "user": email,
                "allow": "Company",
                "for_value": company
            }
        ):
            perm = frappe.get_doc({
                "doctype": "User Permission",
                "user": email,
                "allow": "Company",
                "for_value": company,
                "apply_to_all_doctypes": 1
            })
            perm.flags.ignore_permissions = True
            perm.insert()

        frappe.db.commit()

        return {
            "status": "success",
            "message": "Admin user and company created successfully",
            "email": email,
            "company": company
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Create Admin User Failed")
        return {
            "status": "error",
            "message": str(e)
        }
