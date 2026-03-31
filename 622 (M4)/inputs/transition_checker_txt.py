import pandas as pd

print("Script started")

#define column names matching the tab-separated txt layout (16 columns, no row_id)
col_names = [
    "freq", "unc1", "unc2",
    "v1_upper", "v2_upper", "v3_upper", "l_upper", "J_upper", "parity_upper",
    "v1_lower", "v2_lower", "v3_lower", "l_lower", "J_lower", "parity_lower",
    "ref"
]

#load tab-separated txt file (no header row)
df = pd.read_csv(
    "Working Transitions.txt",
    sep="\t",
    header=None,
    engine="python",
    usecols=range(16)
)

df.columns = [
    "wavenumber",
    "unc_original",
    "unc_current",
    "v1_upper",
    "v2_upper",
    "v3_upper",
    "l_upper",
    "J_upper",
    "parity_upper",
    "v1_lower",
    "v2_lower",
    "v3_lower",
    "l_lower",
    "J_lower",
    "parity_lower",
    "source",
]

#export original txt content as xlsx
df.to_excel(
    "OCS_original_structured_finalcheck.xlsx",
    index=False
)

violations_dict = {}

#check rigorous E1 selection rules + state validity
for idx, row in df.iterrows():

    row_violations = []

    #extract quantum numbers
    Ju = int(row["J_upper"])
    Jl = int(row["J_lower"])
    dJ = Ju - Jl

    pu = str(row["parity_upper"]).strip().lower()
    pl = str(row["parity_lower"]).strip().lower()

    lu = int(row["l_upper"])
    ll = int(row["l_lower"])

    v2u = int(row["v2_upper"])
    v2l = int(row["v2_lower"])

    #allowed: ΔJ = 0, ±1 ; forbidden: J=0 ↔ 0
    if abs(dJ) > 1 or (Ju == 0 and Jl == 0):
        row_violations.append("Forbidden ΔJ")

    #ΔJ = 0  → e ↔ f only, ΔJ = ±1 → e ↔ e or f ↔ f only
    if dJ == 0 and pu == pl:
        row_violations.append("Parity forbidden for ΔJ=0")

    if abs(dJ) == 1 and pu != pl:
        row_violations.append("Parity forbidden for ΔJ=±1")

    #allowed: Δℓ = 0, ±1
    if abs(lu - ll) > 1:
        row_violations.append("Forbidden Δℓ")

    #ℓ ≤ v2 constraint (state validity)
    if lu > v2u or ll > v2l:
        row_violations.append("ℓ > v2")

    #ℓ = 0 parity constraint (state validity)
    if (lu == 0 and pu == "f") or (ll == 0 and pl == "f"):
        row_violations.append("ℓ=0 with f parity")

    #ℓ ≤ J constraint (state validity)
    if abs(lu) > Ju or abs(ll) > Jl:
        row_violations.append("ℓ > J")

    #v2 - ℓ must be even (state validity)
    if (v2u - abs(lu)) % 2 != 0:
        row_violations.append("v2-ℓ parity forbidden (upper)")

    if (v2l - abs(ll)) % 2 != 0:
        row_violations.append("v2-ℓ parity forbidden (lower)")
    
    #label violations with hash
    if row_violations:
        violations_dict[idx] = "; ".join(row_violations)

#add violations column to original dataframe
df["violations"] = df.index.map(violations_dict)

#keep only rows that violate at least one rule
forbidden_df = df[df["violations"].notna()]

#export detailed forbidden transitions
forbidden_df.to_excel(
    "OCS_forbidden_with_reasons_finalcheck.xlsx",
    index=False
)

print(f"Exported {len(forbidden_df)} forbidden transitions")