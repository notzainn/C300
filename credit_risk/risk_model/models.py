from django.db import models

# Create user input fields for storing of prediction result
class UserInput(models.Model):
    cash = models.FloatField()
    total_inventory = models.FloatField()
    non_current_asset = models.FloatField()
    current_liability = models.FloatField()
    gross_profit = models.FloatField()
    retained_earnings = models.FloatField()
    earnings_before_interest = models.FloatField()
    dividends_per_share = models.FloatField()
    total_stockholders_equity = models.FloatField()
    total_market_value = models.FloatField()
    total_revenue = models.FloatField()
    net_cash_flow = models.FloatField()
    total_long_term_debt = models.FloatField()
    total_interest_and_related_expense = models.FloatField()
    sales_turnover_net = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"UserInput {self.id}" # string representation for admin or debugging
    
# Create model to store predictions based on user input
class Prediction(models.Model):
    user_input = models.OneToOneField(UserInput, on_delete=models.CASCADE)
    risk_rating = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Prediction for UserInput {self.user_input.id}" # Debugging or admin display
