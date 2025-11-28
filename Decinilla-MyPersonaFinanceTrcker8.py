import datetime
import json
import os
from typing import List, Optional


class FinancialRecord:
    def __init__(self, date: datetime.date, description: str, amount: float,
                 due_date: Optional[str] = None, record_type: str = "expense"):
        self.date = date
        self.description = description
        self.amount = amount
        self.due_date = due_date
        self.record_type = record_type  # "expense" or "income"

    def to_dict(self):
        return {
            'date': self.date.isoformat(),
            'description': self.description,
            'amount': self.amount,
            'due_date': self.due_date,
            'record_type': self.record_type
        }

    @classmethod
    def from_dict(cls, data):
        date = datetime.date.fromisoformat(data['date'])
        return cls(date, data['description'], data['amount'],
                   data.get('due_date'), data.get('record_type', 'expense'))

    def __str__(self):
        sign = "+" if self.record_type == "income" else "-"
        due_date_info = f" | Due: {self.due_date}" if self.due_date else ""
        return f"{self.date} | {self.description} | {sign}₱{abs(self.amount):.2f}{due_date_info}"


class FinanceTracker:
    def __init__(self, data_file="financial_data.json"):
        self.plans: List[FinancialRecord] = []
        self.trash_bin: List[FinancialRecord] = []
        self.data_file = data_file
        self.load_data()

    def add_record(self, record: FinancialRecord):
        self.plans.append(record)
        self.save_data()

    def add_plan_interactive(self):
        print("\nAdd New Financial Record")
        while True:
            record_type = input("Enter record type ('plan' or 'allowance'): ").strip().lower()
            if record_type in ("plan", "allowance"):
                record_type = "expense" if record_type == "plan" else "income"
                break
            else:
                print("Invalid record type. Please enter 'plan' or 'allowance'.")

        while True:
            date_str = input("Enter date (MM-DD-YYYY): ").strip()
            try:
                date = datetime.datetime.strptime(date_str, '%m-%d-%Y').date()
                break
            except ValueError:
                print("Invalid date format. Please use MM-DD-YYYY.")

        description = input("Enter description: ").strip()
        if not description:
            print("Description cannot be empty.")
            return

        while True:
            try:
                amount = float(input("Enter amount: "))
                if amount <= 0:
                    print("Invalid Amount. Must be positive.")
                    continue
                break
            except ValueError:
                print("Invalid amount. Please enter a number.")

        due_date = None
        if record_type == "expense":
            due_date = input("Enter due date (optional, press Enter to skip): ").strip()
            if not due_date:
                due_date = None

        record = FinancialRecord(date, description, amount, due_date, record_type)
        self.add_record(record)
        print(f"{'Plan' if record_type == 'expense' else 'Allowance'} record added successfully!")

    def view_plans(self, plans_list: Optional[List[FinancialRecord]] = None):
        plans_to_view = plans_list if plans_list is not None else self.plans
        if not plans_to_view:
            print("No records to display.")
            return

        print(f"\n{'#':<3} {'Date':<12} {'Description':<20} {'Amount':<10} {'Due Date':<15} {'Type':<8}")
        print("-" * 75)
        for i, plan in enumerate(plans_to_view):
            amount_str = f"+₱{plan.amount:.2f}" if plan.record_type == "income" else f"-₱{plan.amount:.2f}"
            due_date = plan.due_date if plan.due_date else "N/A"
            record_type_display = "Allowance" if plan.record_type == "income" else "Plan"
            print(f"{i+1:<3} {plan.date:<12} {plan.description:<20} {amount_str:<10} {due_date:<15} {record_type_display:<8}")

    def calculate_balance(self) -> dict:
        total_income = sum(plan.amount for plan in self.plans if plan.record_type == "income")
        total_expenses = sum(plan.amount for plan in self.plans if plan.record_type == "expense")
        net_balance = total_income - total_expenses
        return {
            'income': total_income,
            'expenses': total_expenses,
            'net_balance': net_balance
        }

    def display_balance_report(self):
        balance = self.calculate_balance()
        print("\n--- Financial Balance Report ---")
        print(f"Total Allowances: ₱{balance['income']:.2f}")
        print(f"Total Plans: ₱{balance['expenses']:.2f}")
        print(f"Net Balance: ₱{balance['net_balance']:.2f}")
        if balance['net_balance'] > 0:
            print("Status: Good. Save more!")
        elif balance['net_balance'] < 0:
            print("Status: ALERT!!! You're out of balance!")
        else:
            print("Status: Zero Balance, don't forget to save!")

    def view_upcoming_due_dates(self):
        upcoming_expenses = [plan for plan in self.plans if plan.record_type == "expense" and plan.due_date]
        if not upcoming_expenses:
            print("No upcoming due dates.")
            return

        print("\nUpcoming Due Dates:")
        for expense in sorted(upcoming_expenses, key=lambda x: x.due_date):
            print(f"- {expense.description}: ₱{expense.amount:.2f} due on {expense.due_date}")

    def delete_plan(self):
        self.view_plans()
        if not self.plans:
            return
        while True:
            try:
                index = int(input("Enter the number of the plan to delete (or 0 to cancel): ")) - 1
                if index == -1:
                    print("Deletion cancelled.")
                    return
                if 0 <= index < len(self.plans):
                    deleted_plan = self.plans.pop(index)
                    self.trash_bin.append(deleted_plan)
                    self.save_data()
                    print(f"Deleted: {deleted_plan.description} (-₱{deleted_plan.amount:.2f})")
                    break
                else:
                    print("Invalid plan number. Please try again.")
            except ValueError:
                print("Invalid input. Please enter a number.")

    def view_trash_bin(self):
        if not self.trash_bin:
            print("Trash bin is empty.")
            return
        print("\n--- Trash Bin ---")
        self.view_plans(self.trash_bin)

    def save_data(self):
        try:
            data = {
                'plans': [plan.to_dict() for plan in self.plans],
                'trash_bin': [plan.to_dict() for plan in self.trash_bin]
            }
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving data: {e}")

    def load_data(self):
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.plans = [FinancialRecord.from_dict(item) for item in data.get('plans', [])]
                    self.trash_bin = [FinancialRecord.from_dict(item) for item in data.get('trash_bin', [])]
        except Exception as e:
            print(f"Error loading data: {e}")


def main():
    tracker = FinanceTracker()
    while True:
        print("\n" + "=" * 50)
        print(" PERSONAL FINANCE TRACKER")
        print("=" * 50)
        print("1. Add Financial Record")
        print("2. View All Records")
        print("3. Balance Report")
        print("4. Upcoming Due Dates")
        print("5. Export Data into File")
        print("6. Exit")
        print("-" * 50)
        choice = input("Enter your choice (1-6): ").strip()
        if choice == '1':
            tracker.add_plan_interactive()
        elif choice == '2':
            tracker.view_plans()
        elif choice == '3':
            tracker.display_balance_report()
        elif choice == '4':
            tracker.view_upcoming_due_dates()
        elif choice == '5':
            tracker.export_data_to_file()
        elif choice == '6':
            print("Thank you for using Personal Finance Tracker!")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
