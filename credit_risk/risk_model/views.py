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
from django.views.decorators.csrf import csrf_exempt
from .models import Prediction, UserInput
import json
from django.contrib import messages
from django.contrib.auth.models import User
from .models import CustomUser
from django.contrib.auth import login, logout
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.messages import get_messages
import re


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
    # Check if the user is logged in
    if 'user_id' not in request.session:
        return redirect('user_login')  # Redirect to login page if not logged in
    
    user = request.session.get('username')
    role = request.session.get('role')
    return render(request, 'risk_model/main_page.html', {'user': user, 'role': role})


from django.contrib.messages import get_messages

def user_login(request):
    # Clear all stale messages
    storage = get_messages(request)
    for _ in storage:
        pass

    # Redirect logged-in users to the main page
    if 'user_id' in request.session:
        return redirect('main_page')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Validate password format (6-digit numerical PIN)
        if not password.isdigit() or len(password) != 6:
            messages.error(request, "Please enter your 6-digit PIN.")
            return redirect('user_login')

        try:
            # Authenticate the user
            user = CustomUser.objects.get(username=username, password=password)
            request.session['user_id'] = user.user_id
            request.session['username'] = user.username
            request.session['role'] = user.role
            return redirect('main_page')
        except CustomUser.DoesNotExist:
            messages.error(request, "Username or password is invalid!")
            return redirect('user_login')

    # If there are no other messages, add the default welcome message
    if not messages.get_messages(request):
        messages.info(request, "Welcome! Please login to get started.")
        
    return render(request, 'risk_model/main_page.html')


def user_logout(request):
    if 'user_id' in request.session:
        request.session.flush()  # Clear all session data
        messages.success(request, "You have been logged out. Please login to get started.")
    return redirect('user_login')  # Redirect to user login page


from django.contrib import messages as saved_messages
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


# Predict Risk View
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

        # 🔹 Retrieve the user_id from the session
        user_id = request.session.get('user_id')

        # 🔹 Ensure the user is logged in
        if not user_id:
            return render(request, 'risk_model/main_page.html', {
                'error': "User must be logged in to predict risk."
            })

        # 🔹 Validate that the user_id exists in the CustomUser table
        try:
            user = CustomUser.objects.get(user_id=user_id)  # ✅ Changed from User to CustomUser
        except CustomUser.DoesNotExist:
            return render(request, 'risk_model/main_page.html', {
                'error': "Invalid user session. Please log in again."
            })

        # 🔹 Save the input data into the UserInput model, linking it to the correct CustomUser
        user_input = UserInput.objects.create(user=user, **input_data)  # ✅ Fixed ForeignKey issue

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
            'user_input': user_input  # Ensures user input is saved with correct user_id
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
    # to restrict access to logged-in Admin users
    if not request.session.get('user_id') or request.session.get('role') != 'Admin':
        messages.error(request, "Access denied. Admins only.")
        return redirect('user_login')  # Redirect to the login page if unauthorized

    try:
        # fetch all predictions with related user input
        predictions = Prediction.objects.select_related('user_input').all()

        # prepare the data to send to the template
        prediction_data = [
            {
                'id': prediction.id,
                'name': f"User Input {prediction.user_input.id}",
                'revenue': getattr(prediction.user_input, 'total_revenue', 'N/A'),  # Safe handling for missing fields
                'risk_category': prediction.risk_rating,
            }
            for prediction in predictions
        ]

        # Pass the predictions to the admin dashboard
        return render(request, 'risk_model/admin.html', {'predictions': prediction_data})
    except Exception as e:
        # Log the error for debugging
        print(f"Error in admin_dashboard: {e}")
        # Return an error page or message
        return render(request, 'risk_model/admin.html', {'error': 'An error occurred while loading the dashboard.'})

def manage(request):
    # to restrict access to logged-in Admin users
    if not request.session.get('user_id') or request.session.get('role') != 'Admin':
        messages.error(request, "Access denied. Admins only.")
        return redirect('user_login')

    # Fetch all CustomUser objects
    users = CustomUser.objects.all()
    return render(request, 'risk_model/manage_users.html', {'users': users})


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

# def admin_login(request):
#     if request.method == 'POST':
#         username = request.POST.get('username')
#         password = request.POST.get('password')
#         # Mock admin login validation
#         if username == 'admin' and password == 'password123':
#             return JsonResponse({'success': True})
#         return JsonResponse({'success': False})
#     return JsonResponse({'error': 'Invalid method'}, status=400)

# function to provide explanation for predicted risk 
def XGB_XAI():
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
        # "cash": 500.0,  # Very low cash reserves
        # "total_inventory": 200000.0,  # High inventory that may not be liquid
        # "non_current_asset": 300000.0,  # High fixed assets that are not easily convertible to cash
        # "current_liability": 250000.0,  # High current liabilities
        # "gross_profit": 50000.0,  # Low gross profit compared to revenue
        # "retained_earnings": -20000.0,  # Negative retained earnings indicating losses
        # "earnings_before_interest": 15000.0,  # Low earnings before interest
        # "dividends_per_share": 0.0,  # No dividend payments, possible financial stress
        # "total_stockholders_equity": 50000.0,  # Low equity
        # "total_market_value": 100000.0,  # Low valuation compared to liabilities
        # "total_revenue": 500000.0,  # Moderate revenue but low profitability
        # "net_cash_flow": -50000.0,  # Negative cash flow, indicating financial trouble
        # "total_long_term_debt": 400000.0,  # High long-term debt burden
        # "total_interest_and_related_expense": 50000.0,  # High interest payments
        # "sales_turnover_net": 400000.0,  # Slow turnover, low efficiency
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

    predicted_risk_binary = model.predict(input_df)[0]
    predicted_risk_rating = reverse_mapping.get(predicted_risk_binary)

    #predicted_risk_proba = model.predict_proba(input_df)[:, 1]

    X_train = data.drop(columns=["Risk Rating"])
    feature_name = X_train.columns

    # XAI using SHAP
    shap_explainer = shap.TreeExplainer(model, feature_perturbation='tree_path_dependent')

    # Create mean shap value using our dataset to be used for comparing
    shap_values = shap_explainer.shap_values(X_train)
    shap_values_mean = np.mean(shap_values, axis=0)

    # Create a shap value for our user's input
    shap_values_input = shap_explainer.shap_values(input_df)
    
    shap_df = pd.DataFrame({
        "Feature": feature_name,
        f"SHAP VALUE ({predicted_risk_rating})": shap_values_input[0, :, predicted_risk_binary],
        "SHAP VALUES (Mean)": shap_values_mean[:, predicted_risk_binary]
    }).sort_values(by=f"SHAP VALUE ({predicted_risk_rating})" , ascending=False)

    recommend_improv(shap_df)


def recommend_improv(shap_df):

    for feature_name, shap_val in enumerate(shap_df.values):
        print(feature_name, shap_val)


def manage_users(request):
    # Ensure only Admin users can access this page
    if not request.user.is_authenticated or getattr(request.user, 'role', '') != 'Admin':
        return redirect('main_page')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        role = request.POST.get('role', 'Default')

        # Validate password length
        if len(password) != 6 or not password.isdigit():
            messages.error(request, "Password must be a 6-digit number.")
            return redirect('manage_users')

        # Add user to database
        CustomUser.objects.create(username=username, password=password, role=role)
        messages.success(request, f"User '{username}' added successfully.")
        return redirect('manage_users')

    # Fetch all users for display
    users = CustomUser.objects.all()
    return render(request, 'risk_model/manage_users.html', {'users': users})

# for adding users
def add_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        role = request.POST.get('role')  # Capture the role from the form

        # Ensure username is unique
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect('manage_users')

        # Create a new user
        CustomUser.objects.create(username=username, password=password, role=role)
        messages.success(request, f"User '{username}' added successfully.")
        return redirect('manage_users')


def delete_user(request, user_id):
    try:
        # Fetch the user based on user_id
        user = get_object_or_404(CustomUser, user_id=user_id)
        username = user.username
        user.delete()  # Delete the user
        messages.success(request, f"User '{username}' deleted successfully.")
    except Exception as e:
        messages.error(request, f"An error occurred while deleting the user: {e}")
    
    # Redirect back to the manage users page
    return redirect('manage_users')

XGB_XAI()

from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa

def export_to_pdf(request):
    # Fetch data from the database
    predictions = Prediction.objects.all()  # Query all company data

    # Prepare context for the template
    context = {
        "predictions": predictions, 
    }

    # Load the HTML template
    template = get_template("risk_model/export_template.html")  # Create this template

    # Render the template with the context
    html = template.render(context)

    # Create PDF response
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="Prediction_Data.pdf"'

    # Convert the HTML to PDF using xhtml2pdf
    pisa_status = pisa.CreatePDF(html, dest=response)

    # Check for errors
    if pisa_status.err:
        return HttpResponse("Error occurred while generating the PDF", status=500)

    return response

@csrf_exempt
def predictions_api(request, id=None):
    if request.method == 'GET':
        try:
            if id:  # Fetch a specific prediction by ID
                prediction = Prediction.objects.select_related('user_input').get(id=id)
                data = {
                    'id': prediction.id,
                    'name': f"User Input {prediction.user_input.id}",  # Properly formatted name
                    'revenue': prediction.user_input.total_revenue,
                    'risk_category': prediction.risk_rating,
                }
                return JsonResponse(data, safe=False)
            else:  # Fetch all predictions
                predictions = Prediction.objects.select_related('user_input').all()
                data = [
                    {
                        'id': prediction.id,
                        'name': f"User Input {prediction.user_input.id}",
                        'revenue': prediction.user_input.total_revenue,
                        'risk_category': prediction.risk_rating,
                    }
                    for prediction in predictions
                ]
                return JsonResponse(data, safe=False)
        except Prediction.DoesNotExist:
            return JsonResponse({'error': 'Prediction not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)

            # Update or create UserInput
            user_input, _ = UserInput.objects.update_or_create(
                id=data.get('user_input_id'),
                defaults={'total_revenue': data['revenue']}
            )

            # Update or create Prediction
            prediction, created = Prediction.objects.update_or_create(
                user_input=user_input,
                defaults={'risk_rating': data['risk_category']}
            )
            return JsonResponse({'status': 'success', 'prediction_id': prediction.id, 'created': created})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    elif request.method == 'PUT':
        try:
            body = json.loads(request.body)

            # Fetch the prediction object
            prediction = Prediction.objects.get(id=id)

            # Update related UserInput fields
            user_input = prediction.user_input
            user_input.total_revenue = body.get('revenue', user_input.total_revenue)  # Update revenue
            user_input.save()

            # Update Prediction fields
            prediction.risk_rating = body.get('risk_category', prediction.risk_rating)
            prediction.save()

            # Prepare updated data for response
            updated_data = {
                'id': prediction.id,
                'name': f"User Input {user_input.id}",
                'revenue': user_input.total_revenue,
                'risk_category': prediction.risk_rating,
            }
            return JsonResponse({'status': 'success', 'data': updated_data})
        except Prediction.DoesNotExist:
            return JsonResponse({'error': 'Prediction not found'}, status=404)
        except Exception as e:
            print("Error:", str(e))  # Log the exact error
            return JsonResponse({'error': str(e)}, status=500)

    elif request.method == 'DELETE':
        try:
            # Delete the prediction object
            Prediction.objects.filter(id=id).delete()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
def new_form_view(request):
    if request.method == 'POST':
        try:
            # Debugging: Print all received POST data
            print("POST Data:", request.POST)

            # Extract and validate input data
            cash = float(request.POST.get('cash', '0').strip())
            total_inventory = float(request.POST.get('total_inventory', '0').strip())
            non_current_asset = float(request.POST.get('non_current_asset', '0').strip())
            current_liability = float(request.POST.get('current_liability', '0').strip())
            gross_profit = float(request.POST.get('gross_profit', '0').strip())
            retained_earnings = float(request.POST.get('retained_earnings', '0').strip())
            earnings_before_interest = float(request.POST.get('earnings_before_interest', '0').strip())
            dividends_per_share = float(request.POST.get('dividends_per_share', '0').strip())
            total_stockholders_equity = float(request.POST.get('total_stockholders_equity', '0').strip())
            total_market_value = float(request.POST.get('total_market_value', '0').strip())
            total_revenue = float(request.POST.get('total_revenue', '0').strip())
            net_cash_flow = float(request.POST.get('net_cash_flow', '0').strip())
            total_long_term_debt = float(request.POST.get('total_long_term_debt', '0').strip())
            total_interest_and_related_expense = float(request.POST.get('total_interest_and_related_expense', '0').strip())
            sales_turnover_net = float(request.POST.get('sales_turnover_net', '0').strip())
            risk_category = request.POST.get('riskCategory', '').strip()  # Risk category remains as a string

            # Save user input data
            user_input = UserInput.objects.create(
                cash=cash,
                total_inventory=total_inventory,
                non_current_asset=non_current_asset,
                current_liability=current_liability,
                gross_profit=gross_profit,
                retained_earnings=retained_earnings,
                earnings_before_interest=earnings_before_interest,
                dividends_per_share=dividends_per_share,
                total_stockholders_equity=total_stockholders_equity,
                total_market_value=total_market_value,
                total_revenue=total_revenue,
                net_cash_flow=net_cash_flow,
                total_long_term_debt=total_long_term_debt,
                total_interest_and_related_expense=total_interest_and_related_expense,
                sales_turnover_net=sales_turnover_net,
            )

            # Save prediction data
            Prediction.objects.create(
                user_input=user_input,
                risk_rating=risk_category
            )

            print(request, "Record successfully saved.")
        
            return redirect(('admin_dashboard'))


        except Exception as e:
            # Log error and show an error message
            print(f"Error saving data: {e}")
            return render(request, 'risk_model/new_form.html', {'error': 'Failed to save data. Please try again.'})

    return render(request, 'risk_model/new_form.html')