import numpy as np
import statsmodels.api as sm
import pandas as pd
import linearmodels.panel as PanelOLS
import pytrends.request as TrendReq
import os

print(os.getcwd())

TRENDS_NUMBERS_PATH = "/Users/matyasvarga-etele/Desktop/2025-2026/EconThesis/DataFrame/google_trends_ai_country_year.csv"  
AIP_PATH            = "/Users/matyasvarga-etele/Desktop/2025-2026/EconThesis/DataFrame/aip.xlsx"                              
GDP_PATH            = "/Users/matyasvarga-etele/Desktop/2025-2026/EconThesis/DataFrame/GDP_growth.xlsx"                       
HDI_PATH            = "/Users/matyasvarga-etele/Desktop/2025-2026/EconThesis/DataFrame/HDI.xlsx"                               
OUTPUT_PATH         = "/Users/matyasvarga-etele/Desktop/2025-2026/EconThesis/DataFrame/full.xlsx"

df_trends = pd.read_csv("google_trends_ai_country_year.csv")
df_ai = pd.read_excel("/Users/matyasvarga-etele/Desktop/2025-2026/EconThesis/DataFrame/aip.xlsx")
df_growth= pd.read_excel("/Users/matyasvarga-etele/Desktop/2025-2026/EconThesis/DataFrame/GDP_growth.xls")
df_econ_dev= pd.read_excel("/Users/matyasvarga-etele/Desktop/2025-2026/EconThesis/DataFrame/HDI.xlsx")

print(df_ai.head())
print(df_ai.columns)
df_ai = df_ai[["AI Preparedness Index (Index)", 2023]]  
df_ai = df_ai.rename(columns={
    "AI Preparedness Index (Index)": "country",
    2023: "ai_readiness_2023"
})
print(df_ai.head())

df = df_trends.merge(
    df_ai,
    on="country",
    how="left"
)
print(df[df["country"] == "Albania"].head())
print(df)
print(df["ai_readiness_2023"].isna().sum())
print(set(df_trends["country"]) - set(df_ai["country"]))
