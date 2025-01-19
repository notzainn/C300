import numpy as np
import pandas as pd
import pickle as pkl
import os
from django.http import JsonResponse
from django.shortcuts import render
from .models import Company, UserInput, Prediction # import models for saving User Input and predictions
import json

# Load trained XG boost model
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
model_path = os.path.join(BASE_DIR, 'machine_learning', 'updated_xgb_model.pkl')

# Load the model once when the app starts
def load_model():
    with open(model_path, 'rb') as model_file:
        model = pkl.load(model_file)
    return model

custom_mapping = {
    'In Default': 5,
    'Highest Risk': 4,
    'High Risk': 3,
    'Medium Risk': 2,
    'Low Risk': 1,
    'Lowest Risk': 0
}

reverse_mapping = {value: key for key, value in custom_mapping.items()}  # Reverse mapping for predictions

model = load_model()

def dummy_view(request):
    return render(request, 'risk_model/dummy.html')

def main_page(request):
    return render(request, 'risk_model/main_page.html')

# # View to handle user input and return prediction - THIS WAS ORIGINALLY FOR TESTING, CAN DELETE IF NO NEED ANYM
# def predict_risk(request):
#     #if request.method == "POST":
#         # Extract user inputs from the request (assuming JSON format)
#         #input_data = request.POST.get('input_data')  # Or request.body for JSON input
#         input_data = {
#             "Cash": 50000.0,  # Example: $50,000
#             "Total Inventory": 120000.0,  # Example: $120,000
#             "Non-Current Asset": 100000.0,
#             "Current Liability": 80000.0,  # Example: $80,000
#             "Gross Profit": 250000.0,  # Example: $250,000
#             "Retained Earnings": 100000.0,  # Example: $100,000
#             "Earnings before interest": 75000.0,  # Example: $75,000
#             "Dividends per Share": 2.5,  # Example: $2.50
#             "Total Stockholders Equity": 300000.0,  # Example: $300,000
#             "Total Market Value": 500000.0,  # Example: $500,000
#             "Total Revenue": 1000000.0,  # Example: $1,000,000
#             "Net Cash Flow": 150000.0,  # Example: $150,000
#             "Total Long-Term Debt": 200000.0,  # Example: $200,000
#             "Total Interest and Related Expense": 25000.0,  # Example: $25,000
#             "Sales Turnover (Net)": 900000.0,  # Example: $900,000
#         }


# View to handle form submissions and make predictions
def predict_risk(request):
    if request.method == "POST":
        input_data = {
            "Cash": float(request.POST['cash']),
            "Total Inventory": float(request.POST['total_inventory']),
            "Non-Current Asset": float(request.POST['non_current_asset']),
            "Current Liability": float(request.POST['current_liability']),
            "Gross Profit": float(request.POST['gross_profit']),
            "Retained Earnings": float(request.POST['retained_earnings']),
            "Earnings before interest": float(request.POST['earnings_before_interest']),
            "Dividends per Share": float(request.POST['dividends_per_share']),
            "Total Stockholders Equity": float(request.POST['total_stockholders_equity']),
            "Total Market Value": float(request.POST['total_market_value']),
            "Total Revenue": float(request.POST['total_revenue']),
            "Net Cash Flow": float(request.POST['net_cash_flow']),
            "Total Long-Term Debt": float(request.POST['total_long_term_debt']),
            "Total Interest and Related Expense": float(request.POST['total_interest_and_related_expense']),
            "Sales Turnover (Net)": float(request.POST['sales_turnover_net']),
        }

        # Save the input data into the UserInput model
        user_input = UserInput.objects.create(
            cash=input_data["Cash"],
            total_inventory=input_data["Total Inventory"],
            non_current_asset=input_data["Non-Current Asset"],
            current_liability=input_data["Current Liability"],
            gross_profit=input_data["Gross Profit"],
            retained_earnings=input_data["Retained Earnings"],
            earnings_before_interest=input_data["Earnings before interest"],
            dividends_per_share=input_data["Dividends per Share"],
            total_stockholders_equity=input_data["Total Stockholders Equity"],
            total_market_value=input_data["Total Market Value"],
            total_revenue=input_data["Total Revenue"],
            net_cash_flow=input_data["Net Cash Flow"],
            total_long_term_debt=input_data["Total Long-Term Debt"],
            total_interest_and_related_expense=input_data["Total Interest and Related Expense"],
            sales_turnover_net=input_data["Sales Turnover (Net)"]
        )

        ratios = calculateRatios(input_data)

        combined_data = {**input_data, **ratios}
        features = {
            'Cash': combined_data["Cash"],
            'Earnings Before Interest': combined_data["Earnings before interest"],
            'Gross Profit (Loss)': combined_data["Gross Profit"],
            'Retained Earnings': combined_data["Retained Earnings"],
            'EBTI Margin (Revenue)': combined_data["EBTI Margin"],
            'Dividends per Share - Pay Date - Calendar': combined_data["Dividends per Share"],
            'Total Stockholders Equity': combined_data["Total Stockholders Equity"],
            'Total Market Value (Fiscal Years)': combined_data["Total Market Value"],
            'Total Revenue': combined_data["Total Revenue"],
            'Net Cash Flow': combined_data["Net Cash Flow"],
            'Debt to Equity Ratio': combined_data["Debt_to_Equity"],
            'Return on Asset': combined_data["Return on Asset Ratio"],
            'Interest Coverage': combined_data["Interest Coverage"],
            'Current Ratio': combined_data["Current Ratio"],
            'Return on Equity': combined_data["Return on Equity"],
            'Quick Ratio': combined_data["Quick Ratio"]
        }

        input_df = pd.DataFrame([features])

        risk_rating_binary = model.predict(input_df)[0]
        risk_rating = reverse_mapping.get(risk_rating_binary, "unknown")

        # saving prediction results to the database
        Prediction.objects.create(
            user_input = user_input,
            risk_rating = risk_rating
        )

         # return the prediction result to the user
        return render(request, 'risk_model/show_prediction.html', {'prediction': risk_rating})
    
    # render input form if the request is get
    return render(request, 'risk_model/main_page.html') 

def calculateRatios(data):
    ebti_margin = round(data["Earnings before interest"] / data["Total Revenue"], 2)
    debt_to_equity = round(data["Total Long-Term Debt"] / data["Total Stockholders Equity"], 2)
    return_on_asset = round(data["Earnings before interest"] / (data["Cash"] + data["Total Inventory"] + data["Non-Current Asset"]), 2)
    interest_coverage = round(data["Total Interest and Related Expense"] / data["Earnings before interest"], 2)
    current_ratio = round((data["Cash"] + data["Total Inventory"]) / data["Current Liability"], 2)
    return_on_equity = round(((data["Sales Turnover (Net)"]) - (data["Total Revenue"] - data["Gross Profit"]) 
                              - data["Total Interest and Related Expense"]) / data["Total Stockholders Equity"], 2)
    quick_ratio = round(data["Cash"] / data["Current Liability"], 2)

    ratios = {
        "EBTI Margin": ebti_margin, 
        "Debt_to_Equity": debt_to_equity, 
        "Return on Asset Ratio": return_on_asset,
        "Interest Coverage": interest_coverage, 
        "Current Ratio": current_ratio, 
        "Return on Equity": return_on_equity, 
        "Quick Ratio": quick_ratio
    }

    return ratios

def admin_dashboard(request):
    return render(request, 'risk_model/admin.html')  # Replace 'app_name' with your actual app name

from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
# API for CRUD operations
def companies_api(request):
    if request.method == 'GET':
        try:
            companies = list(Company.objects.values('id', 'name', 'revenue', 'risk_category'))
            return JsonResponse(companies, safe=False)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            company, created = Company.objects.update_or_create(
                name=data['name'],
                defaults={
                    'revenue': data['revenue'],
                    'risk_category': data['riskCategory']
                }
            )
            return JsonResponse({'status': 'success', 'created': created})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    elif request.method == 'DELETE':
        try:
            data = json.loads(request.body)
            Company.objects.filter(id=data['id']).delete()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        # Mock admin login validation
        if username == 'admin' and password == 'password123':
            return JsonResponse({'success': True})
        return JsonResponse({'success': False})
    return JsonResponse({'error': 'Invalid method'}, status=400)