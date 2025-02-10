import numpy as np
import pandas as pd
import pickle as pkl
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import shap
import os
import markdown
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.contrib.auth import login, logout
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.messages import get_messages
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.shortcuts import render
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from .models import Company, UserInput, Prediction, CustomUser # Import models for saving User Input and predictions
from django.views.decorators.csrf import csrf_exempt
import json

# Load trained XG boost model
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
model_path = os.path.join(BASE_DIR, 'machine_learning', 'updated_xgb_model.pkl')
data_path = os.path.join(BASE_DIR, 'machine_learning', 'data.pkl')
static_path = os.path.join(BASE_DIR, 'risk_model', 'static', 'images')

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
        company_name = request.POST.get('company_name', '').strip()
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

        # Retrieve the user_id from the session
        user_id = request.session.get('user_id')

        # Ensure the user is logged in
        if not user_id:
            return render(request, 'risk_model/main_page.html', {
                'error': "User must be logged in to predict risk."
            })

        # Validate that the user_id exists in the CustomUser table
        try:
            user = CustomUser.objects.get(user_id=user_id)  # change user to custom user
        except CustomUser.DoesNotExist:
            return render(request, 'risk_model/main_page.html', {
                'error': "Invalid user session. Please log in again."
            })

        # 🔹 Save the input data into the UserInput model, linking it to the correct CustomUser
        user_input = UserInput.objects.create(user=user, company_name=company_name, **input_data)  # to fix foreign key issue

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

        results = XGB_XAI(input_df)

        # Predict risk rating
        risk_rating_binary = model.predict(input_df)[0]
        risk_rating = reverse_mapping.get(risk_rating_binary, "unknown")

        shap_plot_url = "/static/images/shap_waterfall.png"

        # Render prediction results
        return render(request, 'risk_model/show_prediction.html', {
            'prediction': risk_rating,
            'user_input': user_input,  # Pass user input for saving functionality
            'shap_waterfall_plot': shap_plot_url,
            'waterfall_explanation': results["explanation"],
            "recommendations": results["recommendations"]
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
                'user_input_id': prediction.user_input.id,
                'name': prediction.user_input.company_name or 'Unnamed Company',
                'revenue': getattr(prediction.user_input, 'total_revenue', 'N/A'),  # Safe handling for missing fields
                'risk_category': prediction.risk_rating,
                'id': prediction.id,
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


# function to provide explanation for predicted risk 
def XGB_XAI(input_df):
    
    predicted_risk_binary = model.predict(input_df)[0]
    predicted_risk_rating = reverse_mapping.get(predicted_risk_binary)

    X_train = data.drop(columns=["Risk Rating"])
    feature_name = X_train.columns

    # XAI using SHAP
    shap_explainer = shap.TreeExplainer(model, feature_perturbation='tree_path_dependent')

    # Create a shap value for our user's input
    shap_values_input = shap_explainer.shap_values(input_df)

    # Get the average feature value of user in "Lowest Risk" Risk Rating
    lowest_risk_avg = data[data["Risk Rating"] == 0].drop(columns=["Risk Rating"]).mean()

    shap_interpretation = pd.DataFrame({
        "Feature": feature_name,
        "User Input": input_df.iloc[0].values,
        "Lowest Risk Avg": lowest_risk_avg.values,
        f"SHAP VALUE ({predicted_risk_rating})": shap_values_input[0, :, predicted_risk_binary],
        f"SHAP VALUE ({reverse_mapping.get(0)})": shap_values_input[0, :, 0],
    }).round(2)

    shap_plot_path = os.path.join(static_path, 'shap_waterfall.png')

    shap_explanation = shap.Explanation(
                        values=shap_values_input[0, :, predicted_risk_binary], 
                        base_values=shap_explainer.expected_value[predicted_risk_binary], 
                        data=input_df.iloc[0].values, 
                        feature_names=feature_name
                    )


    # Generate and save the SHAP waterfall plot
    plt.figure(figsize=(8, 6))
    shap.plots.waterfall(shap_explanation, show=False)
    plt.title("SHAP Waterfall Plot")
    plt.savefig(shap_plot_path, bbox_inches="tight")  # Save to static folder
    plt.close("all")


    suggestions = indiv_assesment(shap_interpretation, predicted_risk_rating)
    return suggestions

def indiv_assesment(shap_interpretation: pd.DataFrame, user_rating):
    recommendations = []

    sort_interpretation = shap_interpretation.sort_values(by=(f"SHAP VALUE ({user_rating})"), ascending=False)


    top_positive = sort_interpretation.head(3)
    top_negative = sort_interpretation.tail(3)
    explanation = f"**Key Influences on Your Risk Rating Include:**\n"
    explanation += "\n**Increased Risk Factors:**\n\n"
    for index, row in top_positive.iterrows():
        explanation += f" - {row['Feature']}: **{row[f'SHAP VALUE ({user_rating})']:.2f}** (Contributed to higher risk)\n"
    
    explanation += "\n**Decreased Risk Factors:**\n\n"
    for index, row in top_negative.iterrows():
        explanation += f" - {row['Feature']}: **{row[f'SHAP VALUE ({user_rating})']:.2f}** (Helped lower your risk)\n"
    explanation += "To reduce your risk, focus on improving the factors that increase your risk score"


    for _, row in sort_interpretation.head(16).iterrows():
        feature = row["Feature"]
        user_val = row["User Input"]
        low_risk_avg = row["Lowest Risk Avg"]
        shap_user = row[f"SHAP VALUE ({user_rating})"]

        suggestions = ""
        if user_val < low_risk_avg:
            if feature == "Current Ratio":
                suggestions = "A low current ratio of can indicate that a company has insufficient short-term liquidity. Consider increasing current asset or to reduce short-term liabilities to help enhance liquidity."
            elif feature == "Interest Coverage":
                suggestions = "A low interest coverage suggest that a company has difficulty covering their interest expense from operating expenses. Consider reducing debt, or improving profitability to ensure better financial security."
            elif feature == "Quick Ratio":
                suggestions = "Quick ratio is lower than the benchmark, which means your company may not have enough liquid assets to cover short-term liabilites. Improving cash flow, and reducing reliance on inventory may help reduce risk."
            elif feature == "EBTI Margin (Revenue)":
                suggestions = "A low EBTI Margin may suggest that a company has reduced profitability before interest and tax expenses. Consider improving operational efficiency."
            elif feature == "Return on Equity":
                suggestions = "A low Return on Equity (ROE) suggest that your company is not generating sufficient returns on shareholder investments. Focus on increasing net income, improving asset efficiency, or optimizing financial management strategy."
            elif feature == "Return on Asset":
                suggestions = "A low Return on Asset suggests that your company is not utilizing its asset efficiently to generate profit. Consider reducing unnecessary expenses, optimize asset utilization, op improving operational efficiency."
            elif feature == "Total Market Value (Fiscal Years)":
                suggestions = "A low market value may suggest undervaluation or lower investor confidence. Improving financial performance, or increasing brand value may help."
        elif feature == "Debt to Eequity Ratio" and user_val > low_risk_avg:
            suggestions = "A high Debt-to-Equity ratio  suggests that your company relies heavily on debt financing. Consider lowering debt reliance for operating, increasing equity via reinvestments."


        if suggestions:
            recommendations.append({
                "feature": feature,
                "user_value": round(user_val,2),
                "lowest_risk_avg": round(low_risk_avg, 2),
                "shap_value": round(shap_user, 2),
                "suggestions": suggestions
            })

    return {
        "explanation": markdown.markdown(explanation),
        "recommendations": recommendations,
    }

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
                    'user_input_id': prediction.user_input.id,
                    'name': prediction.user_input.company_name or 'Unnamed Company',
                    'revenue': prediction.user_input.total_revenue,
                    'risk_category': prediction.risk_rating,
                }
                return JsonResponse(data, safe=False)
            else:  # Fetch all predictions
                predictions = Prediction.objects.select_related('user_input').all()
                data = [
                    {
                        'id': prediction.id,
                        'user_input_id': prediction.user_input.id,
                        'name': prediction.user_input.company_name or 'Unnamed Company',
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
                defaults={'total_revenue': data['revenue'],
                          'name': data.get('name', '') }
            )

            # Update or create Prediction
            prediction, created = Prediction.objects.update_or_create(
                user_input=user_input,
                defaults={'risk_rating': data['risk_category'],
                          'name': data.get('name', '') }
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
            user_input.company_name = body.get('name', user_input.company_name) 
            user_input.save()

            

            # Update Prediction fields
            
            prediction.risk_rating = body.get('risk_category', prediction.risk_rating)
            prediction.save()

            # Prepare updated data for response
            updated_data = {
                'id': prediction.id,
                'user_input_id': prediction.user_input.id, 
                'name': prediction.user_input.company_name,
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
            # Retrieve the user_id from session
            user_id = request.session.get('user_id')
            if not user_id:
                return render(request, 'risk_model/new_form.html', {'error': 'User must be logged in to save data.'})

            # Fetch the CustomUser instance
            try:
                user = CustomUser.objects.get(user_id=user_id)
            except CustomUser.DoesNotExist:
                return render(request, 'risk_model/new_form.html', {'error': 'Invalid user session. Please log in again.'})

            # Debugging: Print all received POST data
            print("POST Data:", request.POST)

            # Extract and validate input data
            name = request.POST.get('company_name', '').strip()
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
                user=user,
                company_name=name,
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
                risk_rating=risk_category,
            )

            print("Record successfully saved.")

            return redirect('admin_dashboard')

        except Exception as e:
            # Log error and show an error message
            print(f"Error saving data: {e}")
            return render(request, 'risk_model/new_form.html', {'error': 'Failed to save data. Please try again.'})

    return render(request, 'risk_model/new_form.html')

def mypredictions_view(request):
    if 'user_id' not in request.session:
        return redirect('user_login')
    
    user_id = request.session.get('user_id')

    predictions = Prediction.objects.filter(user_input__user__user_id=user_id)
    return render(request, 'risk_model/mypredictions.html', {'predictions': predictions}) 



@csrf_exempt
def update_prediction(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            prediction_id = data.get('user_id')
            name = data.get('name')
            revenue = data.get('revenue')
            risk_category = data.get('risk_category')

            if not all([prediction_id, revenue, risk_category]):
                return JsonResponse({'error': 'Missing required fields'}, status=400)

            # Fix the query to properly reference the ForeignKey
            prediction = Prediction.objects.get(id=prediction_id)
            prediction.user_input.total_revenue = revenue
            prediction.risk_rating = risk_category
            prediction.user_input.company_name = name
            prediction.user_input.save()
            prediction.save()

            return JsonResponse({'message': 'Prediction updated successfully!'}, status=200)

        except Prediction.DoesNotExist:
            return JsonResponse({'error': 'Prediction not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    
@csrf_exempt
def delete_prediction(request):
    if request.method == 'POST':
        try:
            # Parse the incoming data
            data = json.loads(request.body)
            prediction_id = data.get('id')  # Get the prediction ID from the request

            if not prediction_id:
                return JsonResponse({'error': 'Missing prediction ID'}, status=400)

            # Find and delete the prediction
            prediction = Prediction.objects.get(id=prediction_id)
            prediction.delete()

            return JsonResponse({'message': 'Prediction deleted successfully!'}, status=200)

        except Prediction.DoesNotExist:
            return JsonResponse({'error': 'Prediction not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    
from django.conf import settings    
def generate_pdf(request, prediction_id):
    # Fetch the prediction data
    try:
        prediction = Prediction.objects.get(id=prediction_id)
    except Prediction.DoesNotExist:
        return HttpResponse("Prediction not found", status=404)

    # Fetch user input data linked to the prediction
    try:
        user_input = prediction.user_input
    except AttributeError:
        return HttpResponse("User input data not found for the prediction.", status=404)

    # Define SHAP plot path
    shap_plot_path = os.path.join(settings.BASE_DIR, 'risk_model', 'static', 'images', 'shap_waterfall.png')
    shap_plot_path = shap_plot_path.replace('\\', '/')

    # Ensure the SHAP plot file exists
    if not os.path.exists(shap_plot_path):
        return HttpResponse("SHAP plot image not found", status=404)

    # Prepare raw input data
    raw_input_data = {
        "cash": user_input.cash,
        "total_inventory": user_input.total_inventory,
        "non_current_asset": user_input.non_current_asset,
        "current_liability": user_input.current_liability,
        "gross_profit": user_input.gross_profit,
        "retained_earnings": user_input.retained_earnings,
        "earnings_before_interest": user_input.earnings_before_interest,
        "dividends_per_share": user_input.dividends_per_share,
        "total_stockholders_equity": user_input.total_stockholders_equity,
        "total_market_value": user_input.total_market_value,
        "total_revenue": user_input.total_revenue,
        "net_cash_flow": user_input.net_cash_flow,
        "total_long_term_debt": user_input.total_long_term_debt,
        "total_interest_and_related_expense": user_input.total_interest_and_related_expense,
        "sales_turnover_net": user_input.sales_turnover_net,
    }

    # Call the calculateRatios function to compute ratios
    try:
        calculated_ratios = calculateRatios(raw_input_data)
    except Exception as e:
        return HttpResponse(f"Error calculating ratios: {e}", status=500)

    # Combine raw input data and calculated ratios
    combined_data = {**raw_input_data, **calculated_ratios}

    # Prepare features for the model
    features = {
        'Cash': combined_data["cash"],
        'Earnings Before Interest': combined_data["earnings_before_interest"],
        'Gross Profit (Loss)': combined_data["gross_profit"],
        'Retained Earnings': combined_data["retained_earnings"],
        'EBTI Margin (Revenue)': combined_data["EBTI Margin"],  # Calculated dynamically
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

    input_df = pd.DataFrame([features])

    try:
        shap_results = XGB_XAI(input_df)
    except Exception as e:
        return HttpResponse(f"Error generating explanations: {e}", status=500)
    
    shap_explanation = shap_results.get("explanation", "No explanation available")
    shap_recommendations = shap_results.get("recommendations", [])

    key_influences = shap_explanation 
    
    
    # Prepare the data for the template
    context = {
        'prediction': prediction.risk_rating,
        'shap_waterfall_plot': shap_plot_path,
        'key_influences': key_influences,
        'recommendations': shap_recommendations,
    }


    # Load the HTML template
    template = get_template("risk_model/genreport.html")  # Create this template
    html = template.render(context)

    # Create a PDF response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Prediction_Report_{prediction_id}.pdf"'

    # Convert the HTML to a PDF
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Error occurred while generating PDF', status=500)

    return response 

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
    
@csrf_exempt
def edit_user(request, user_id):
    if request.method == 'POST':
        try:
            user = CustomUser.objects.get(user_id=user_id)
            user.username = request.POST.get('username')
            user.password = request.POST.get('password')  # Make sure to hash passwords for security
            user.role = request.POST.get('role')
            user.save()
            # Return JSON response with updated data
            return JsonResponse({
                'message': 'User updated successfully',
                'user_id': user_id,
                'username': user.username,
                'role': user.role
            }, status=200)
        except CustomUser.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

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