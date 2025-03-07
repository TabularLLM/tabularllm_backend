def intial_prompt_with_few_shot():
    example_data_sample = "Creditability,Account Balance,Duration of Credit (month),Payment Status of Previous Credit,Purpose,Credit Amount,Value Savings/Stocks,Length of current employment,Instalment per cent,Sex & Marital Status,Guarantors,Duration in Current Address,Most Valuable Asset,Age (years),Type of Apartment ,Occupation,No of dependents,Foreign Worker \
        1,< 0 DM,18,Critical account,Furniture/Equipment,1049,< 100 DM,< 1 year,4,Female: Divorced/Separated/Married,None,> 3 years,Savings agreement/Life insurance,21,Rent,Skilled Employee/Official,1,Yes \
        1,< 0 DM,9,Critical Account,New car,2799,< 100 DM,1 <= ... < 4 years,2,Male: Single,None,1 < ... <= 2 years,Real estate,36,Rent,Skilled Employee/Official,2,Yes \
        1,0 < Balance < 200 DM,12,All Credits at this Bank Paid Back Duly,Business,841,100 <= ... < 500 DM,4 <= ... < 7 years,2,Female: Divorced/Separated/Married,None,> 3 years,Real estate,23,Rent,Unskilled - Resident,1,Yes \
        1,< 0 DM,12,Critical Account,New car,2122,< 100 DM,1 <= ... < 4 years,3,Male: Single,None,1 < ... <= 2 years,Real estate,39,Rent,Unskilled - Resident,2,No \
        1,< 0 DM,12,Critical Account,New car,2171,< 100 DM,1 <= ... < 4 years,4,Male: Single,None,> 3 years,Savings agreement/Life insurance,38,Own,Unskilled - Resident,1,No \
        1,< 0 DM,10,Critical Account,New car,2241,< 100 DM,< 1 year,1,Male: Single,None,2 < ... <= 3 years,Real estate,48,Rent,Unskilled - Resident,2,No \
        1,< 0 DM,8,Critical Account,New car,3398,< 100 DM,4 <= ... < 7 years,1,Male: Single,None,> 3 years,Real estate,39,Own,Unskilled - Resident,1,No \
        1,< 0 DM,6,Critical Account,New car,1361,< 100 DM,Unemployed,4,Female: Divorced/Separated/Married,None,> 3 years,Car or other,65,Own,Unemployed/Unskilled - Non-resident,1,Yes"
    
    example_prompt = f"Consider the data set {example_data_sample}, in this one I have identified 18 features, with 13 categorical and 5 numerical features. The data set has 9 records. \
          The numerical features are: 'Duration of Credit (month)', 'Credit Amount', 'Installment per cent', 'Age (years)', 'No of dependents'. The categorical features are: 'Creditability', 'Account Balance', 'Payment Status of Previous Credit', 'Purpose', 'Value Savings/Stock'.\
          The average values for the numerical features are: 'Duration of Credit (month)': 11.33, 'Credit Amount': 1865.33, 'Installment per cent': 2.67, 'Age (years)': 35.33, 'No of dependents': 1.44. \
          The count of categories for the categorical features are: 'Creditability': {{1: 9}}, 'Account Balance': {{'< 0 DM': 7, '0 < Balance < 200 DM': 1, 'No Checking Account': 1}}, 'Payment Status of Previous Credit': {{'Critical Account': 9}}, 'Purpose': {{'Furniture/Equipment': 1, 'New car': 6, 'Business': 1, 'Radio/Television': 1}}, 'Value Savings/Stock': {{'< 100 DM': 9}}. \
          Based on my approach and calculations, given the new dataset I've uploaded, conduct a similar analysis and provide the results."
    
    return example_prompt
