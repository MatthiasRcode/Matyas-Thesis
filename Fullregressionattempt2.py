import re
import unicodedata
import numpy as np
import pandas as pd

TRENDS_CSV_PATH = "google_trends_ai_country_year.csv"  
AIP_PATH            = "/Users/matyasvarga-etele/Desktop/2025-2026/EconThesis/DataFrame/aip.xlsx"                       
GDP_PATH            = "/Users/matyasvarga-etele/Desktop/2025-2026/EconThesis/DataFrame/GDP_growth.xlsx"                     
HDI_PATH            = "/Users/matyasvarga-etele/Desktop/2025-2026/EconThesis/DataFrame/HDI.xlsx"                              
OUTPUT_PATH         = "/Users/matyasvarga-etele/Desktop/2025-2026/EconThesis/DataFrame/full_pluschanges_df.xlsx"

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

for d in (df_trends, df_ai, gdp_long, df_hdi):
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
for d in (df_trends, df_ai, gdp_long, df_hdi):
    d["country"] = d["country"].replace(name_fix)

gdp_2024 = (
    gdp_long[gdp_long["year"] == 2024][["country", "gdp_pc_growth"]]
    .rename(columns={"gdp_pc_growth": "gdp_2024"})
)
gdp_long = gdp_long.merge(gdp_2024, on="country", how="left")
gdp_long.loc[gdp_long["year"] == 2025, "gdp_pc_growth"] = gdp_long.loc[gdp_long["year"] == 2025, "gdp_2024"]
gdp_long = gdp_long.drop(columns=["gdp_2024"])

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

print("Saved:", OUTPUT_PATH)
print("Shape:", df_full.shape)
print(df_full.head())

print(df_full[df_full["country"]=="Albania"][["year","gdp_pc_growth","hdi"]].tail(5))
