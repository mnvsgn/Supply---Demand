import os
import pandas as pd
import numpy as np

os.makedirs("sample_data", exist_ok=True)
np.random.seed(42)

# 1. Retail Store Sales (Multi-Product Daily CSV)
dates = pd.date_range(start="2024-01-01", periods=180, freq="D")
products = ["SKU-101 (Beverages)", "SKU-202 (Bakery)", "SKU-303 (Dairy)"]
stores = ["Store-A (Downtown)", "Store-B (Suburbs)"]

records = []
for d in dates:
    day_of_week = d.dayofweek
    # Weekend lift
    weekend_factor = 1.35 if day_of_week in [4, 5, 6] else 1.0
    for prod in products:
        base_demand = 80 if "Beverages" in prod else (55 if "Bakery" in prod else 40)
        trend = (d - dates[0]).days * 0.12
        for st in stores:
            store_mult = 1.2 if "Downtown" in st else 0.95
            noise = np.random.normal(0, 5)
            promo = 1 if np.random.rand() < 0.15 else 0
            promo_lift = 1.25 if promo else 1.0
            
            units = max(5, int((base_demand + trend) * weekend_factor * store_mult * promo_lift + noise))
            unit_price = 4.99 if "Beverages" in prod else (3.49 if "Bakery" in prod else 2.89)
            revenue = round(units * unit_price, 2)
            
            records.append({
                "Date": d.strftime("%Y-%m-%d"),
                "Product_ID": prod,
                "Store_ID": st,
                "Units_Sold": units,
                "Unit_Price": unit_price,
                "Promotion_Active": promo,
                "Revenue": revenue
            })

df_retail = pd.DataFrame(records)
df_retail.to_csv("sample_data/retail_store_sales.csv", index=False)
print("Created sample_data/retail_store_sales.csv with", len(df_retail), "rows")

# 2. Daily Aggregate Demand (Single-Series Clean CSV)
agg_dates = pd.date_range(start="2024-03-01", periods=120, freq="D")
agg_records = []
for i, d in enumerate(agg_dates):
    seasonal = 20 * np.sin(2 * np.pi * i / 7) # weekly cycle
    trend = i * 0.4
    noise = np.random.normal(0, 8)
    demand = max(10, int(150 + seasonal + trend + noise))
    agg_records.append({
        "Date": d.strftime("%Y-%m-%d"),
        "Daily_Demand": demand,
        "Day_Name": d.strftime("%A"),
        "Is_Weekend": 1 if d.dayofweek >= 5 else 0
    })

df_agg = pd.DataFrame(agg_records)
df_agg.to_csv("sample_data/daily_aggregate_demand.csv", index=False)
print("Created sample_data/daily_aggregate_demand.csv with", len(df_agg), "rows")

# 3. Warehouse FMCG Inventory & Demand (Excel XLSX format)
fmcg_dates = pd.date_range(start="2024-01-01", periods=90, freq="D")
fmcg_records = []
for d in fmcg_dates:
    for cat in ["Packaged Foods", "Personal Care"]:
        base = 120 if cat == "Packaged Foods" else 75
        noise = np.random.normal(0, 10)
        daily_units = max(15, int(base + noise))
        lead_time = 7 if cat == "Packaged Foods" else 14
        on_hand = max(50, int(daily_units * lead_time * 1.5 + np.random.normal(0, 30)))
        
        fmcg_records.append({
            "Order_Date": d.strftime("%Y-%m-%d"),
            "Category": cat,
            "SKU": f"SKU-{cat[:4].upper()}-01",
            "Units_Ordered": daily_units,
            "Inventory_On_Hand": on_hand,
            "Lead_Time_Days": lead_time
        })

df_fmcg = pd.DataFrame(fmcg_records)
df_fmcg.to_excel("sample_data/warehouse_fmcg_demand.xlsx", index=False)
print("Created sample_data/warehouse_fmcg_demand.xlsx with", len(df_fmcg), "rows")
