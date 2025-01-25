import numpy as np
import pandas as pd
import xgboost as xgb
import pickle as pkl
import matplotlib.pyplot as plt
import seaborn as sbn
from sklearn.metrics import roc_curve, confusion_matrix, auc
import shap
import lime
import lime.lime_tabular
import os
import re
from django.http import JsonResponse
from django.shortcuts import render
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from .models import Company, UserInput, Prediction  # Import models for saving User Input and predictions
import json


# Load trained XG boost model
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
model_path = os.path.join(BASE_DIR, 'machine_learning', 'updated_xgb_model.pkl')
data_path = os.path.join(BASE_DIR, 'machine_learning', 'data.pkl')

# Load the model once when the app starts
def load_model():
    with open(model_path, 'rb') as model_file:
        model = pkl.load(model_file)
    return model

def load_data():
    with open(data_path, 'rb') as data_file:
        data = pkl.load(data_file)
    return data

custom_mapping = {
    'In Default': 5,
    'Highest Risk': 4,
    'High Risk': 3,
    'Medium Risk': 2,
    'Low Risk': 1,
    'Lowest Risk': 0
}

reverse_mapping = {value: key for key, value in custom_mapping.items()}  # Reverse mapping for predictions

# Initialise/load the model & data into a variable
model = load_model()
data = load_data()

def dummy_view(request):
    return render(request, 'risk_model/dummy.html')

def main_page(request):
    return render(request, 'risk_model/main_page.html')

# View to handle saving of records
def main_page(request):
    return render(request, 'risk_model/main_page.html')

# View to handle saving of records
def save_prediction(request):
    if request.method == "POST":
        # Get the UserInput ID and the predicted risk rating from the POST request
        user_input_id = request.POST.get('user_input_id')  # Get UserInput reference
        prediction = request.POST.get('prediction')  # Get the risk rating

        # Retrieve the related UserInput instance
        user_input = get_object_or_404(UserInput, id=user_input_id)

        # Save the prediction
        Prediction.objects.create(
            user_input=user_input,
            risk_rating=prediction
        )

        # Add a success message
        saved_messages.success(request, "Record successfully saved.")

        # Redirect back to the main page
        return redirect(reverse('main_page'))

    return JsonResponse({'error': 'Invalid request method'}, status=400)


# View to handle form submissions and make predictions
def predict_risk(request):
    if request.method == "POST":
        # Input data mapped to match the UserInput model fields
        input_data = {
            "cash": float(request.POST['cash']),
            "total_inventory": float(request.POST['total_inventory']),
            "non_current_asset": float(request.POST['non_current_asset']),
            "current_liability": float(request.POST['current_liability']),
            "gross_profit": float(request.POST['gross_profit']),
            "retained_earnings": float(request.POST['retained_earnings']),
            "earnings_before_interest": float(request.POST['earnings_before_interest']),
            "dividends_per_share": float(request.POST['dividends_per_share']),
            "total_stockholders_equity": float(request.POST['total_stockholders_equity']),
            "total_market_value": float(request.POST['total_market_value']),
            "total_revenue": float(request.POST['total_revenue']),
            "net_cash_flow": float(request.POST['net_cash_flow']),
            "total_long_term_debt": float(request.POST['total_long_term_debt']),
            "total_interest_and_related_expense": float(request.POST['total_interest_and_related_expense']),
            "sales_turnover_net": float(request.POST['sales_turnover_net']),
        }

        # Save the input data into the UserInput model
        user_input = UserInput.objects.create(**input_data)

        # Calculate financial ratios
        ratios = calculateRatios(input_data)

        # Combine input data and calculated ratios
        combined_data = {**input_data, **ratios}
        features = {
            'Cash': combined_data["cash"],
            'Earnings Before Interest': combined_data["earnings_before_interest"],
            'Gross Profit (Loss)': combined_data["gross_profit"],
            'Retained Earnings': combined_data["retained_earnings"],
            'EBTI Margin (Revenue)': combined_data["EBTI Margin"],
            'Dividends per Share - Pay Date - Calendar': combined_data["dividends_per_share"],
            'Total Stockholders Equity': combined_data["total_stockholders_equity"],
            'Total Market Value (Fiscal Years)': combined_data["total_market_value"],
            'Total Revenue': combined_data["total_revenue"],
            'Net Cash Flow': combined_data["net_cash_flow"],
            'Debt to Equity Ratio': combined_data["Debt_to_Equity"],
            'Return on Asset': combined_data["Return on Asset Ratio"],
            'Interest Coverage': combined_data["Interest Coverage"],
            'Current Ratio': combined_data["Current Ratio"],
            'Return on Equity': combined_data["Return on Equity"],
            'Quick Ratio': combined_data["Quick Ratio"],
        }

        # Create a DataFrame for prediction
        input_df = pd.DataFrame([features])

        # Predict risk rating
        risk_rating_binary = model.predict(input_df)[0]
        risk_rating = reverse_mapping.get(risk_rating_binary, "unknown")

        # Render prediction results
        return render(request, 'risk_model/show_prediction.html', {
            'prediction': risk_rating,
            'user_input': user_input  # Pass user input for saving functionality
        })

    # Render input form if the request method is GET
    return render(request, 'risk_model/main_page.html')

def calculateRatios(data):
    ebti_margin = round(data["earnings_before_interest"] / data["total_revenue"], 2)
    debt_to_equity = round(data["total_long_term_debt"] / data["total_stockholders_equity"], 2)
    return_on_asset = round(data["earnings_before_interest"] / (data["cash"] + data["total_inventory"] + data["non_current_asset"]), 2)
    interest_coverage = round(data["total_interest_and_related_expense"] / data["earnings_before_interest"], 2)
    current_ratio = round((data["cash"] + data["total_inventory"]) / data["current_liability"], 2)
    return_on_equity = round(((data["sales_turnover_net"]) - (data["total_revenue"] - data["gross_profit"]) 
                              - data["total_interest_and_related_expense"]) / data["total_stockholders_equity"], 2)
    quick_ratio = round(data["cash"] / data["current_liability"], 2)

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


# function to provide explanation for predicted risk 
def xgb_XAI():
    input_data = {
        "cash": 50000.0,  # Lowercase keys
        "total_inventory": 120000.0,
        "non_current_asset": 100000.0,
        "current_liability": 80000.0,
        "gross_profit": 250000.0,
        "retained_earnings": 100000.0,
        "earnings_before_interest": 75000.0,
        "dividends_per_share": 2.5,
        "total_stockholders_equity": 300000.0,
        "total_market_value": 500000.0,
        "total_revenue": 1000000.0,
        "net_cash_flow": 150000.0,
        "total_long_term_debt": 200000.0,
        "total_interest_and_related_expense": 25000.0,
        "sales_turnover_net": 900000.0,
    }

    ratios = calculateRatios(input_data)

    combined_data = {**input_data, **ratios}
    features = {
        "Cash": combined_data["cash"],
        "Earnings Before Interest": combined_data["earnings_before_interest"],
        "Gross Profit (Loss)": combined_data["gross_profit"],
        "Retained Earnings": combined_data["retained_earnings"],
        "EBTI Margin (Revenue)": combined_data["EBTI Margin"],
        "Dividends per Share - Pay Date - Calendar": combined_data["dividends_per_share"],
        "Total Stockholders Equity": combined_data["total_stockholders_equity"],
        "Total Market Value (Fiscal Years)": combined_data["total_market_value"],
        "Total Revenue": combined_data["total_revenue"],
        "Net Cash Flow": combined_data["net_cash_flow"],
        "Debt to Equity Ratio": combined_data["Debt_to_Equity"],
        "Return on Asset": combined_data["Return on Asset Ratio"],
        "Interest Coverage": combined_data["Interest Coverage"],
        "Current Ratio": combined_data["Current Ratio"],
        "Return on Equity": combined_data["Return on Equity"],
        "Quick Ratio": combined_data["Quick Ratio"],
    }

    input_df = pd.DataFrame([features])

    predicted_risk = model.predict(input_df)
    predicted_risk_proba = model.predict_proba(input_df)[:, 1]

    print(f"Predicted Risk: {reverse_mapping.get(predicted_risk[0])} \nPredicted Risk Probability: {predicted_risk_proba[0]}")

    X_train = data.drop(columns=["Risk Rating"])

    explainer = lime.lime_tabular.LimeTabularExplainer(
        training_data=X_train.values,
        mode="classification",
        class_names=["Lowest Risk", "Low Risk", "Medium Risk", "High Risk", "Highest Risk", "In Default"],
        feature_names=X_train.columns,
        discretize_continuous=True,
    )

    explanation = explainer.explain_instance(input_df.values[0], model.predict_proba)

    feature_impt = explanation.as_list()

    sorted_importance = sorted(feature_impt, key=lambda x: abs(x[1]), reverse=True)

    top10 = sorted_importance[:10]
    
    # for feature in top10:
    #     print(f"Feature Criteria: {feature[0]} \nFeature Importance: {round(feature[1],2)} \n")

    reccomendation(input_df, top10)


def reccomendation(input_df, feature_crit):

    for criteria, importance in feature_crit:
        
        # regular expression to identify criterias
        feature_re = r"([\d.+])*\s*(<=|=>|<|>)*\s*([a-zA-Z\s()-]+)\s*(<=|>=|<|>)\s*([\d.]+)"
        # split all based on matches
        matches = re.findall(feature_re, criteria)

        print(matches, ", ", criteria)
        
        condition_bool = True

        # for condition in conditions:
        #     if '>' in condition:
        #         feature_name, threshold = condition.split(' > ')
        #         operator = '>'
        #     elif '<' in condition:
        #         feature_name, threshold = condition.split(' < ')
        #         operator = '<'
        #     elif '>=' in condition:
        #         feature_name, threshold = condition.split(' >= ')
        #         operator = '>='
        #     elif '<=' in condition:
        #         feature_name, threshold = condition.split(' <= ')
        #         operator = '<='
            
        #     threshold = float(threshold)

        #     print(f"{feature_name}: {operator}")



xgb_XAI()

from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa

def export_to_pdf(request):
    # Fetch data from the database
    companies = Company.objects.all()  # Query all company data

    # Prepare context for the template
    context = {
        "companies": companies, 
    }

    # Load the HTML template
    template = get_template("risk_model/export_template.html")  # Create this template

    # Render the template with the context
    html = template.render(context)

    # Create PDF response
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="Company_Data.pdf"'

    # Convert the HTML to PDF using xhtml2pdf
    pisa_status = pisa.CreatePDF(html, dest=response)

    # Check for errors
    if pisa_status.err:
        return HttpResponse("Error occurred while generating the PDF", status=500)

    return response