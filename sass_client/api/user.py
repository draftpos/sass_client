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
        assign_first_client()

        doc = frappe.get_all(
            "Client Details",
            fields=["name"],
            order_by="creation asc",
            limit=1
        )

        if doc:
            d = frappe.get_doc("Client Details", doc[0].name)
            d.assigned_to = 1   # or True
            d.save()
            frappe.db.commit()
            print(f"Updated {d.name}")
        else:
            print("No records found")

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

@frappe.whitelist(allow_guest=True)
def assign_first_client():
    """
    Update the first Client Details record to mark assigned as True
    """
    try:

        client = frappe.get_all(
            "Client Details",
            order_by="creation asc",
            limit_page_length=1,
            fields=["name", "assigned"]
        )

        if not client:
            return {"status": "error", "message": "No Client Details records found"}

        doc = frappe.get_doc("Client Details", client[0].name)
        doc.assigned = True  # flip to True
        doc.flags.ignore_permissions = True
        doc.save()
        frappe.db.commit()

        return {
            "status": "success",
            "message": "First client record updated",
            "client": doc.name,
            "assigned": doc.assigned
        }

    except Exception as e:
        frappe.log_error(str(e), "Assign First Client Failed")
        return {"status": "error", "message": str(e)}
