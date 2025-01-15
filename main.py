import pickle as pkl
import pandas as pd
import numpy as np

# export data file 
with open('data.pkl', 'rb') as file:
    dataset = pkl.load(file)

# export model file
with open('updated_xgb_model.pkl', 'rb') as file:
    xgb_model = pkl.load(file)

custom_mapping = {
    'In Default': 5,
    'Highest Risk': 4,
    'High Risk': 3,
    'Medium Risk': 2,
    'Low Risk': 1,
    'Lowest Risk': 0
}

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

example_data = {
    "Cash": 50000.0,  # Example: $50,000
    "Total Inventory": 120000.0,  # Example: $120,000
    "Non-Current Asset": 100000.0,
    "Current Liability": 80000.0,  # Example: $80,000
    "Gross Profit": 250000.0,  # Example: $250,000
    "Retained Earnings": 100000.0,  # Example: $100,000
    "Earnings before interest": 75000.0,  # Example: $75,000
    "Dividends per Share": 2.5,  # Example: $2.50
    "Total Stockholders Equity": 300000.0,  # Example: $300,000
    "Total Market Value": 500000.0,  # Example: $500,000
    "Total Revenue": 1000000.0,  # Example: $1,000,000
    "Net Cash Flow": 150000.0,  # Example: $150,000
    "Total Long-Term Debt": 200000.0,  # Example: $200,000
    "Total Interest and Related Expense": 25000.0,  # Example: $25,000
    "Sales Turnover (Net)": 900000.0,  # Example: $900,000
}



ratios = calculateRatios(example_data)

# combine both dictionaries into one
combined_data = {**example_data, **ratios}

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

input_data = pd.DataFrame([features])

risk_rating_binary = xgb_model.predict(input_data)[0]
reversed_mapping = {value: key for key, value in custom_mapping.items()}
risk_rating = reversed_mapping.get(risk_rating_binary, "unknown")

print(f"The predicted risk rating: {risk_rating}")
