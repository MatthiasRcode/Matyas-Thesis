#--------------------------------------------------------------------------------------------------------------------
# Modules and datapaths
import re
import unicodedata
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt

TRENDS_CSV_PATH = "google_trends_ai_country_year.csv"  
AIP_PATH            = "/Users/matyasvarga-etele/Desktop/2025-2026/EconThesis/DataFrame/aip.xlsx"                       
GDP_PATH            = "/Users/matyasvarga-etele/Desktop/2025-2026/EconThesis/DataFrame/GDP_growth.xlsx"                     
HDI_PATH            = "/Users/matyasvarga-etele/Desktop/2025-2026/EconThesis/DataFrame/HDI.xlsx"                              
OUTPUT_PATH         = "/Users/matyasvarga-etele/Desktop/2025-2026/EconThesis/DataFrame/full_pluschanges_df.xlsx"
INVEST_PATH = "/Users/matyasvarga-etele/Desktop/2025-2026/EconThesis/DataFrame/investment.xlsx"
#--------------------------------------------------------------------------------------------------------------------
# Getting the DataFrame df
def clean_country(s: str) -> str:
    if pd.isna(s):
        return s
    s = str(s).strip().replace("\u00a0", " ")
    s = unicodedata.normalize("NFKC", s)
    s = re.sub(r"\s+", " ", s)
    return s

df_trends = pd.read_csv(TRENDS_CSV_PATH)
df_trends["year"] = df_trends["year"].astype(int)
df_trends["artificial_intelligence"] = pd.to_numeric(
    df_trends["artificial_intelligence"], errors="coerce"
)

aip_raw = pd.read_excel(AIP_PATH)
df_ai = aip_raw.rename(columns={
    "AI Preparedness Index (Index)": "country",
    2023: "ai_readiness_2023"
})[["country", "ai_readiness_2023"]]

gdp_wide = pd.read_excel(GDP_PATH)
year_cols = [c for c in gdp_wide.columns if re.fullmatch(r"\d{4}", str(c))]

gdp_long = gdp_wide.melt(
    id_vars=["Country Name", "Country Code"],
    value_vars=year_cols,
    var_name="year",
    value_name="gdp_pc_growth",
).rename(columns={
    "Country Name": "country",
    "Country Code": "iso3"
})
gdp_long["year"] = gdp_long["year"].astype(int)
gdp_long["gdp_pc_growth"] = pd.to_numeric(gdp_long["gdp_pc_growth"], errors="coerce")

hdi_raw = pd.read_excel(HDI_PATH)
df_hdi = hdi_raw[
    hdi_raw["indicatorCode"].astype(str).str.lower().eq("hdi")
].rename(columns={"value": "hdi"})[
    ["country", "year", "hdi"]
]
df_hdi["year"] = df_hdi["year"].astype(int)
df_hdi["hdi"] = pd.to_numeric(df_hdi["hdi"], errors="coerce")

inv_wide = pd.read_excel(INVEST_PATH)

id_vars_inv = ["Country Name"]
if "Country Code" in inv_wide.columns:
    id_vars_inv.append("Country Code")

year_cols_inv = [c for c in inv_wide.columns if re.fullmatch(r"\d{4}", str(c))]

inv_long = inv_wide.melt(
    id_vars=id_vars_inv,
    value_vars=year_cols_inv,
    var_name="year",
    value_name="investment",
).rename(columns={"Country Name": "country"})

inv_long["year"] = inv_long["year"].astype(int)
inv_long["investment"] = pd.to_numeric(inv_long["investment"], errors="coerce")

for d in (df_trends, df_ai, gdp_long, df_hdi, inv_long):
    d["country"] = d["country"].apply(clean_country)

name_fix = {
    "Türkiye, Republic of": "Turkey",
    "Côte d'Ivoire": "Cote d'Ivoire",
    "Korea, Republic of": "Korea, Rep.",
    "Russian Federation": "Russia",
    "Slovak Republic": "Slovakia",
    "Lao P.D.R.": "Lao PDR",
    "Congo, Republic of": "Congo, Rep.",
    "Congo, Republic of ": "Congo, Rep.",
    "Congo, Dem. Rep. of the": "Congo, Dem. Rep.",
    "Gambia, The": "Gambia",
    "Bahamas, The": "Bahamas",
    "Hong Kong SAR": "Hong Kong SAR, China",
    "China, People's Republic of": "China",
    "North Macedonia ": "North Macedonia",
}
for d in (df_trends, df_ai, gdp_long, df_hdi, inv_long):
    d["country"] = d["country"].replace(name_fix)

gdp_2024 = (
    gdp_long[gdp_long["year"] == 2024][["country", "gdp_pc_growth"]]
    .rename(columns={"gdp_pc_growth": "gdp_2024"})
)
gdp_long = gdp_long.merge(gdp_2024, on="country", how="left")
gdp_long.loc[gdp_long["year"] == 2025, "gdp_pc_growth"] = gdp_long.loc[gdp_long["year"] == 2025, "gdp_2024"]
gdp_long = gdp_long.drop(columns=["gdp_2024"])

#investment 2025 equal to 2024
inv_2024 = (
    inv_long[inv_long["year"] == 2024][["country", "investment"]]
    .rename(columns={"investment": "investment_2024"})
)
inv_long = inv_long.merge(inv_2024, on="country", how="left")
inv_long.loc[inv_long["year"] == 2025, "investment"] = inv_long.loc[
    inv_long["year"] == 2025, "investment_2024"
]
inv_long = inv_long.drop(columns=["investment_2024"])

hdi_2023 = (
    df_hdi[df_hdi["year"] == 2023][["country", "hdi"]]
    .rename(columns={"hdi": "hdi_2023"})
)
df_hdi = df_hdi.merge(hdi_2023, on="country", how="left")
mask_hdi_fill = df_hdi["year"].isin([2024, 2025]) & df_hdi["hdi"].isna()
df_hdi.loc[mask_hdi_fill, "hdi"] = df_hdi.loc[mask_hdi_fill, "hdi_2023"]
df_hdi = df_hdi.drop(columns=["hdi_2023"])

df_full = df_trends.merge(df_ai, on="country", how="left")
df_full = df_full.merge(
    gdp_long[["country", "year", "gdp_pc_growth"]],
    on=["country", "year"],
    how="left"
)
df_full = df_full.merge(
    df_hdi[["country", "year", "hdi"]],
    on=["country", "year"],
    how="left"
)

df_full = df_full.merge(
    inv_long[["country", "year", "investment"]],
    on=["country", "year"],
    how="left"
)

df_full["investment"] = pd.to_numeric(df_full["investment"], errors="coerce")

df_full["year"] = df_full["year"].astype(int)
df_full["gdp_pc_growth"] = pd.to_numeric(df_full["gdp_pc_growth"], errors="coerce")
df_full["hdi"] = pd.to_numeric(df_full["hdi"], errors="coerce")

def force_gdp_2025_equals_2024(g):
    v2024 = g.loc[g["year"] == 2024, "gdp_pc_growth"]
    if not v2024.dropna().empty:
        g.loc[g["year"] == 2025, "gdp_pc_growth"] = v2024.dropna().iloc[0]
    return g

def fill_hdi_2024_2025_with_2023_if_missing(g):
    v2023 = g.loc[g["year"] == 2023, "hdi"]
    if not v2023.dropna().empty:
        base = v2023.dropna().iloc[0]
        mask = g["year"].isin([2024, 2025]) & g["hdi"].isna()
        g.loc[mask, "hdi"] = base
    return g

df_full = (
    df_full.groupby("country", group_keys=False)
           .apply(force_gdp_2025_equals_2024)
           .groupby("country", group_keys=False)
           .apply(fill_hdi_2024_2025_with_2023_if_missing)
)

df_full["ai_trends_std"] = df_full.groupby("country")[
    "artificial_intelligence"
].transform(
    lambda x: (x - x.mean()) / x.std(ddof=0) if x.std(ddof=0) not in (0, np.nan) else np.nan
)

df_full["ai_readiness_std"] = (
    (df_full["ai_readiness_2023"] - df_full["ai_readiness_2023"].mean())
    / df_full["ai_readiness_2023"].std(ddof=0)
)

df_full["ai_x_readiness"] = df_full["ai_trends_std"] * df_full["ai_readiness_std"]
df_full["ai_x_hdi"] = df_full["ai_trends_std"] * df_full["hdi"]
df_full["ai_idx_x_hdi"] = df_full["ai_x_readiness"] * df_full["hdi"]

df_full = df_full.sort_values(["country", "year"]).reset_index(drop=True)
df_full.to_excel(OUTPUT_PATH, index=False)
#--------------------------------------------------------------------------------------------------------------------
# For df checks
#print("Saved:", OUTPUT_PATH)
#print("Shape:", df_full.shape)
#print(df_full.head())
#print(df_full[df_full["country"]=="Albania"][["year","gdp_pc_growth","hdi"]].tail(5))
# investment variable completeness
#print("Missing investment share:", df_full["investment"].isna().mean())
#print(df_full[df_full["year"].isin([2024, 2025])][["country","year","investment"]].dropna().head(10))
#--------------------------------------------------------------------------------------------------------------------
# Descriptive Statistics
df = pd.read_excel("/Users/matyasvarga-etele/Desktop/2025-2026/EconThesis/DataFrame/full_pluschanges_df.xlsx")

variables = [
    "gdp_pc_growth",
    "ai_trends_std",
    "ai_readiness_std",
    "hdi",
    "investment"
]

df_desc = df[variables]

desc_stats = df_desc.describe().T

desc_stats["observations"] = df_desc.count()

desc_stats = desc_stats[
    ["observations", "mean", "std", "min", "25%", "50%", "75%", "max"]
]

print(desc_stats)

correlation_matrix = df_desc.corr()

print("\nCorrelation Matrix:\n")
print(correlation_matrix)

with pd.ExcelWriter("descriptive_statistics.xlsx") as writer:
    desc_stats.to_excel(writer, sheet_name="Descriptive_Statistics")
    correlation_matrix.to_excel(writer, sheet_name="Correlation_Matrix")

print("\nSaved file: descriptive_statistics.xlsx")
#--------------------------------------------------------------------------------------------------------------------
# Baseline interaction regression
model = smf.ols(
    formula="""
    gdp_pc_growth ~ ai_trends_std + hdi + ai_x_hdi
    + C(country) + C(year)
    """,
    data=df_full
).fit(cov_type="HC1")  # heteroskedasticity-robust SEs

print(model.summary())
#--------------------------------------------------------------------------------------------------------------------
# Model with investment variable as control variable
model_inv = smf.ols(
    formula="""
    gdp_pc_growth ~ ai_trends_std + hdi + ai_x_hdi + investment
    + C(country) + C(year)
    """,
    data=df_full
).fit(cov_type="HC1")  # heteroskedasticity-robust SEs

print(model_inv.summary())

#--------------------------------------------------------------------------------------------------------------------
# Mean, low, and high HDI
hdi_mean = df_full["hdi"].mean()
hdi_low = df_full["hdi"].quantile(0.25)
hdi_high = df_full["hdi"].quantile(0.75)

beta_ai = model.params["ai_trends_std"]
beta_inter = model.params["ai_x_hdi"]

print("Marginal effect of AI at low HDI:",
      beta_ai + beta_inter * hdi_low)

print("Marginal effect of AI at mean HDI:",
      beta_ai + beta_inter * hdi_mean)

print("Marginal effect of AI at high HDI:",
      beta_ai + beta_inter * hdi_high)
#--------------------------------------------------------------------------------------------------------------------
# Illustrations
# Linear results
beta_ai = model_inv.params["ai_trends_std"]
beta_inter = model_inv.params["ai_x_hdi"]
hdi_vals = np.linspace(df_full["hdi"].min(), df_full["hdi"].max(), 100)
marginal_effect = beta_ai + beta_inter * hdi_vals
plt.figure()
plt.plot(hdi_vals, marginal_effect)
plt.axhline(0)
plt.xlabel("Human Development Index (HDI)")
plt.ylabel("Marginal effect of AI adoption on GDP per capita growth")
plt.title("Marginal effect of AI adoption across levels of development")
#plt.show()

# HDI Bar chart
df_full["hdi_group"] = pd.qcut(df_full["hdi"], q=2, labels=["Low HDI", "High HDI"])
group_means = df_full.groupby("hdi_group")[["gdp_pc_growth", "ai_trends_std"]].mean()
print(group_means)
group_means.plot(kind="bar")
plt.ylabel("Mean value")
plt.title("Average AI adoption and growth by development group")
plt.show()

#--------------------------------------------------------------------------------------------------------------------
# Regression table

model_base = smf.ols(
    "gdp_pc_growth ~ ai_trends_std + hdi + ai_x_hdi + C(country) + C(year)",
    data=df_full
).fit(cov_type="HC1")

model_inv = smf.ols(
    "gdp_pc_growth ~ ai_trends_std + hdi + ai_x_hdi + investment + C(country) + C(year)",
    data=df_full
).fit(cov_type="HC1")

main_vars = ["ai_trends_std", "hdi", "ai_x_hdi", "investment"]

def stars(p):
    if pd.isna(p):
        return ""
    if p < 0.01: return "***"
    if p < 0.05: return "**"
    if p < 0.10: return "*"
    return ""

def fmt(x, digits=3):
    return "" if pd.isna(x) else f"{x:.{digits}f}"

def get_row(model, var):
    if var not in model.params.index:
        return {"coef": "", "se": "", "pval": ""}
    coef = model.params[var]
    se   = model.bse[var]       
    pval = model.pvalues[var]   
    return {
        "coef": f"{fmt(coef)}{stars(pval)}",
        "se": f"({fmt(se)})",
        "pval": fmt(pval)
    }

rows = []
for v in main_vars:
    r1 = get_row(model_base, v)
    r2 = get_row(model_inv, v)
    rows.append({
        "variable": v,
        "(1) Baseline coef": r1["coef"],
        "(1) Baseline SE": r1["se"],
        "(1) Baseline pval": r1["pval"],
        "(2) + Investment coef": r2["coef"],
        "(2) + Investment SE": r2["se"],
        "(2) + Investment pval": r2["pval"],
    })

table = pd.DataFrame(rows).set_index("variable")

info = pd.DataFrame(
    {
        "(1) Baseline coef": ["Yes", "Yes", int(model_base.nobs), round(model_base.rsquared, 3)],
        "(1) Baseline SE":   ["", "", "", ""],
        "(1) Baseline pval": ["", "", "", ""],
        "(2) + Investment coef": ["Yes", "Yes", int(model_inv.nobs), round(model_inv.rsquared, 3)],
        "(2) + Investment SE":   ["", "", "", ""],
        "(2) + Investment pval": ["", "", "", ""],
    },
    index=["Country FE", "Year FE", "Observations", "R-squared"]
)

final_table = pd.concat([table, info])

final_table.to_excel("regression_table.xlsx")
print("Exported regression table to: regression_table.xlsx")