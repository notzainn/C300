from django.db import models

# Model to store user inputs for credit risk prediction
class UserInput(models.Model):
    cash = models.FloatField()  # User's cash amount
    total_inventory = models.FloatField()  # Total inventory
    non_current_asset = models.FloatField()  # Non-current assets
    current_liability = models.FloatField()  # Current liabilities
    gross_profit = models.FloatField()  # Gross profit
    retained_earnings = models.FloatField()  # Retained earnings
    earnings_before_interest = models.FloatField()  # Earnings before interest
    dividends_per_share = models.FloatField()  # Dividends per share
    total_stockholders_equity = models.FloatField()  # Total stockholders' equity
    total_market_value = models.FloatField()  # Total market value
    total_revenue = models.FloatField()  # Total revenue
    net_cash_flow = models.FloatField()  # Net cash flow
    total_long_term_debt = models.FloatField()  # Total long-term debt
    total_interest_and_related_expense = models.FloatField()  # Total interest and related expense
    sales_turnover_net = models.FloatField()  # Sales turnover (net)
    created_at = models.DateTimeField(auto_now_add=True)  # Automatically store the creation time

    def __str__(self):
        return f"UserInput {self.id} - Created on {self.created_at}"  # string representation for debugging/admin


# Model to store predictions based on user inputs
class Prediction(models.Model):
    user_input = models.OneToOneField(
        UserInput, 
        on_delete=models.CASCADE,  # Ensure cascading deletes to maintain database integrity
        related_name="prediction"  # Adds a reverse relation to `UserInput`
    )
    risk_rating = models.CharField(max_length=50) 
    created_at = models.DateTimeField(auto_now_add=True)  # Automatically store the prediction creation time

    def __str__(self):
        return f"Prediction for UserInput {self.user_input.id} - Risk: {self.risk_rating}"


# Model to store company information for CRUD operations
class Company(models.Model):
    name = models.CharField(max_length=255, unique=True)  # Company name (unique constraint ensures no duplicates)
    revenue = models.FloatField()  # Company revenue as a float
    risk_category = models.CharField(
        max_length=50,
        choices=[
            ('Low Risk', 'Low Risk'),
            ('Medium Risk', 'Medium Risk'),
            ('High Risk', 'High Risk'),
        ],  # Predefined choices for risk categories
    )
    created_at = models.DateTimeField(auto_now_add=True)  # Automatically store the creation time

    def __str__(self):
        return f"Company {self.name} - Risk Category: {self.risk_category}"  # Improved representation for admin/debugging
