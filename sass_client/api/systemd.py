import frappe


def after_install():
    site = frappe.local.site
    print(f"🚀 Installed on site: {site}")

def has_saas_client():
    apps = frappe.get_installed_apps()

    print("🔍 Checking installed apps for site:", frappe.local.site)
    print("📦 Installed apps:", apps)

    if "sass_client" in apps:
        print("✅ sass_client IS installed on this site")
        return True
    else:
        print("❌ saas_client is NOT installed on this site")
        return False
