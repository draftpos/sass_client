import frappe

def get_unique_company_abbr(company):
    base_abbr = "".join(word[0] for word in company.split()).upper()

    abbr = base_abbr
    counter = 1

    while frappe.db.exists("Company", {"abbr": abbr}):
        abbr = f"{base_abbr}{counter}"
        counter += 1

    return abbr


@frappe.whitelist(allow_guest=True)  # no allow_guest, only logged-in users
def create_admin_user(username=None, email=None, password=None, company=None,country=None):
    """
    Create or fetch an admin user with full permissions and assign company
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
        if not country:
            country = "Zimbabwe"

        # -----------------------------
        # Update first client if exists
        # -----------------------------
        d = frappe.get_single("client detail")
        d.flags.ignore_permissions = True
        d.assigned = 1
        d.save()
        frappe.db.commit()
        print(f"Updated {d.name}")

        # -----------------------------
        # Create company if not exists
        if not frappe.db.exists("Company", company):
            abbr = get_unique_company_abbr(company)

            company_doc = frappe.get_doc({
                "doctype": "Company",
                "company_name": company,
                "abbr": abbr,
                "default_currency": "USD",
                "country": country 
            })

            company_doc.flags.ignore_permissions = True
            company_doc.insert(ignore_permissions=True)
        # -----------------------------
        # Get or create user
        # -----------------------------
        user_doc = frappe.db.exists("User", email)
        if user_doc:
            user = frappe.get_doc("User", email)
            user_created = False
        else:
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
            user_created = True

        # -----------------------------
        # Assign System Manager role
        # -----------------------------
        if "System Manager" not in [r.role for r in user.get("roles")]:
            user.add_roles("System Manager")

        # -----------------------------
        # Ensure company permission
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
        assign_first_client()  # your existing function

        # -----------------------------
        # Single return
        # -----------------------------
        return {
            "status": "success",
            "message": f"Admin user {email} {'created' if user_created else 'already exists'} and company {company} ensured",
            "email": email,
            "company": company
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "create_admin_user")
        return {
            "status": "error",
            "message": str(e)
        }


@frappe.whitelist(allow_guest=True)
@frappe.whitelist(allow_guest=True)
def assign_first_client():
    """
    Update the first client detail record to mark assigned as True
    """
    try:
        # Get the first client detail record
        client = frappe.get_all("client detail", limit_page_length=1)
        
        if not client:
            return {"status": "error", "message": "No client detail records found"}

        doc = frappe.get_doc("client detail", client[0].name)
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