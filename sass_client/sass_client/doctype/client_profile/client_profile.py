
import frappe
from frappe.utils import getdate, nowdate

class ClientProfile(frappe.model.document.Document):

    def before_save(self):
        self.calculate_days_left()

    def calculate_days_left(self):
        if not self.subscription_end_date:
            self.days_left = 0
            return

        today = getdate(nowdate())
        end_date = getdate(self.subscription_end_date)

        diff = (end_date - today).days

        # Never go negative (optional but recommended)
        self.days_left = max(diff, 0)
