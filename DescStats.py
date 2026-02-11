import pandas as pd

df = pd.read_excel("/Users/matyasvarga-etele/Desktop/2025-2026/EconThesis/DataFrame/full_pluschanges_df.xlsx")

variables = [
    "gdp_pc_growth",
    "ai_trends_std",
    "ai_readiness_std",
    "hdi",
    "ai_x_readiness",
    "ai_x_hdi"
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
