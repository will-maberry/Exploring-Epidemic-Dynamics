
from pathlib import Path
import re
import unicodedata

import geopandas as gpd
import pandas as pd


# Configuration

ROOT = Path(__file__).resolve().parent

TIGER_DIR = ROOT / "tl_2025_us_county"

OUT = ROOT / "Data_Processed"
OUT.mkdir(parents=True, exist_ok=True)

CENSUS_FILE = ROOT / "Data_Raw" / "US-Census.xlsx"

if not CENSUS_FILE.is_file():
    raise FileNotFoundError(
        f"Cannot find Census file: {CENSUS_FILE}"
    )

shapefiles = sorted(TIGER_DIR.glob("*.shp"))

if not shapefiles:
    raise FileNotFoundError(
        f"No shapefile found in {TIGER_DIR}"
    )

preferred = TIGER_DIR / "tl_2025_us_county.shp"

TIGER_FILE = (
    preferred if preferred.exists()
    else shapefiles[0] if len(shapefiles) == 1
    else None
)

if TIGER_FILE is None:
    raise ValueError(
        "Multiple shapefiles found. Specify TIGER_FILE explicitly."
    )

# Geographic adjacency:
# "rook"  = shared boundary segment
# "queen" = shared boundary segment OR corner
ADJACENCY = "rook"

# Shared boundary length threshold in meters
    # Small threshold suppresses tiny geometry artifacts
MIN_SHARED_BORDER_M = 10.0

# EPSG:5070: projected CRS suitable for contiguous-US
    # distance/area calculations.
PROJECTED_CRS = "EPSG:5070"

EXCLUDED_STATE_FIPS = {"02", "15", "11"}

STATE_FIPS = {
    "Alabama": "01",
    "Arizona": "04",
    "Arkansas": "05",
    "California": "06",
    "Colorado": "08",
    "Connecticut": "09",
    "Delaware": "10",
    "Florida": "12",
    "Georgia": "13",
    "Idaho": "16",
    "Illinois": "17",
    "Indiana": "18",
    "Iowa": "19",
    "Kansas": "20",
    "Kentucky": "21",
    "Louisiana": "22",
    "Maine": "23",
    "Maryland": "24",
    "Massachusetts": "25",
    "Michigan": "26",
    "Minnesota": "27",
    "Mississippi": "28",
    "Missouri": "29",
    "Montana": "30",
    "Nebraska": "31",
    "Nevada": "32",
    "New Hampshire": "33",
    "New Jersey": "34",
    "New Mexico": "35",
    "New York": "36",
    "North Carolina": "37",
    "North Dakota": "38",
    "Ohio": "39",
    "Oklahoma": "40",
    "Oregon": "41",
    "Pennsylvania": "42",
    "Rhode Island": "44",
    "South Carolina": "45",
    "South Dakota": "46",
    "Tennessee": "47",
    "Texas": "48",
    "Utah": "49",
    "Vermont": "50",
    "Virginia": "51",
    "Washington": "53",
    "West Virginia": "54",
    "Wisconsin": "55",
    "Wyoming": "56",
}

FIPS_STATE = {
    value: key for key, value in STATE_FIPS.items()
}

POPULATION_COLUMNS = [
    f"population_{year}"
    for year in range(2020, 2026)
]


# Name Normalizing

def normalize(text):
    text = str(text)

    text = unicodedata.normalize("NFKD", text)
    text = "".join(
        char for char in text
        if not unicodedata.combining(char)
    )

    text = text.lower()

    text = re.sub(
        r"\b("
        r"county|parish|borough|"
        r"planning region|census area|"
        r"municipality|municipio|city"
        r")\b",
        "",
        text,
    )

    return re.sub(r"[^a-z0-9]", "", text)


# Distinguish cities from county with same name
def unit_type(name):
    if re.search(r"\bcity\b", str(name), re.I):
        return "city"
    return "county_equivalent"


def matching_key(name, state_fips):
    return (
        str(state_fips).zfill(2)
        + "|"
        + normalize(name)
        + "|"
        + unit_type(name)
    )


# Load TIGER Shapefile

print("Loading TIGER/Line 2025...")

tiger = gpd.read_file(TIGER_FILE)

required = {"GEOID", "STATEFP", "NAME", "geometry"}

missing = required - set(tiger.columns)

if missing:
    raise ValueError(
        f"TIGER missing required columns: {missing}"
    )

tiger["fips"] = tiger["GEOID"].astype(str).str.zfill(5)
tiger["state_fips"] = (
    tiger["STATEFP"].astype(str).str.zfill(2)
)

tiger = tiger[
    tiger["state_fips"].isin(FIPS_STATE)
].copy()

tiger = tiger[
    ~tiger["state_fips"].isin(EXCLUDED_STATE_FIPS)
].copy()

tiger["state"] = tiger["state_fips"].map(FIPS_STATE)

# NAME is generally base name
    # NAMELSAD contains geographic designation such as County/city
tiger["official_name"] = (
    tiger["NAMELSAD"].fillna(tiger["NAME"])
    if "NAMELSAD" in tiger.columns
    else tiger["NAME"]
)

tiger["county"] = (
    tiger["NAME"]
    .str.replace(r"\bcity\b", "", case=False, regex=True)
    .str.strip()
)

tiger["match_key"] = [
    matching_key(name, state)
    for name, state in zip(
        tiger["official_name"],
        tiger["state_fips"],
    )
]

assert tiger["fips"].is_unique, "Duplicate TIGER GEOIDs"
assert tiger["match_key"].is_unique, (
    "Duplicate TIGER geographic matching keys"
)

if tiger.crs is None:
    raise ValueError("TIGER shapefile has no defined CRS")

print(f"TIGER geographic units: {len(tiger):,}")


# Load Census Data

print("Loading Census population estimates...")

raw = pd.read_excel(
    CENSUS_FILE,
    header=None,
)

raw = raw.iloc[
    5:,
    [0, 2, 3, 4, 5, 6, 7],
].copy()

raw.columns = [
    "geography",
    *POPULATION_COLUMNS,
]

raw = raw[
    raw["geography"]
    .astype(str)
    .str.startswith(".")
].copy()

parts = (
    raw["geography"]
    .astype(str)
    .str.lstrip(".")
    .str.rsplit(", ", n=1, expand=True)
)

raw["county_original"] = parts[0].str.strip()
raw["state"] = parts[1].str.strip()

raw["state_fips"] = raw["state"].map(STATE_FIPS)

# Only contiguous 48 states
raw = raw[
    raw["state_fips"].notna()
].copy()

# Display name only
    # Don't use stripped name
raw["county_census"] = (
    raw["county_original"]
    .str.replace(r"\bcity\b", "", case=False, regex=True)
    .str.strip()
)

raw["match_key"] = [
    matching_key(name, state)
    for name, state in zip(
        raw["county_original"],
        raw["state_fips"],
    )
]

for col in POPULATION_COLUMNS:
    raw[col] = pd.to_numeric(
        raw[col],
        errors="coerce",
    ).astype("Int64")

assert raw["match_key"].is_unique, (
    "Duplicate Census geographic matching keys"
)

print(f"Census geographic units: {len(raw):,}")


# Match county population to TIGER

print("Matching Census population to TIGER GEOIDs...")

# Left merge retains every TIGER geographic unit
merged = tiger.merge(
    raw[
        [
            "match_key",
            "county_original",
            *POPULATION_COLUMNS,
        ]
    ],
    on="match_key",
    how="left",
    validate="one_to_one",
    indicator=True,
)

unmatched_tiger = merged[
    merged["_merge"] == "left_only"
].copy()

unmatched_census = raw[
    ~raw["match_key"].isin(tiger["match_key"])
].copy()

# Save both sides for debugging
tiger_diagnostics = pd.DataFrame({
    "source": "TIGER",
    "fips": unmatched_tiger["fips"],
    "state": unmatched_tiger["state"],
    "name": unmatched_tiger["official_name"],
    "match_key": unmatched_tiger["match_key"],
})

census_diagnostics = pd.DataFrame({
    "source": "Census",
    "fips": pd.NA,
    "state": unmatched_census["state"],
    "name": unmatched_census["county_original"],
    "match_key": unmatched_census["match_key"],
})

diagnostics = pd.concat(
    [tiger_diagnostics, census_diagnostics],
    ignore_index=True,
)

diagnostics.to_csv(
    OUT / "unmatched_counties.csv",
    index=False,
)

# Don't invent populations or silently discard
    # geographic units that failed to match
if not diagnostics.empty:
    print(
        f"Unmatched geographic records: "
        f"{len(diagnostics):,}"
    )
    print(
        diagnostics[
            ["source", "state", "name", "match_key"]
        ].head(30).to_string(index=False)
    )
    print(
        "See Data/processed/unmatched_counties.csv"
    )

# Retain full TIGER geography
    # Missing populations remain missing for inspection
counties = merged.drop(columns=["_merge"]).copy()


# Geometry handling

print("Preparing projected county geometries...")

geo = counties[
    ["fips", "geometry"]
].copy()

geo = gpd.GeoDataFrame(
    geo,
    geometry="geometry",
    crs=tiger.crs,
)

geo = geo.to_crs(PROJECTED_CRS)

if geo.geometry.isna().any():
    raise ValueError("Missing TIGER geometries")

if not geo.geometry.is_valid.all():
    print("Repairing invalid geometries...")
    geo["geometry"] = geo.geometry.make_valid()

geo = geo.reset_index(drop=True)

# Geographic center for mapping and simulation
centers = counties[
    ["fips", "geometry"]
].copy()

centers = gpd.GeoDataFrame(
    centers,
    geometry="geometry",
    crs=tiger.crs,
)

centers = centers.to_crs(PROJECTED_CRS)

# representative_point is guaranteed to lie inside polygon
    # Centroid doesn't always due to irregular polygons
centers["geometry"] = centers.geometry.representative_point()

centers = centers.to_crs("EPSG:4326")

center_table = pd.DataFrame({
    "fips": centers["fips"],
    "longitude": centers.geometry.x,
    "latitude": centers.geometry.y,
})

counties = counties.merge(
    center_table,
    on="fips",
    how="left",
    validate="one_to_one",
)


# Build geographic adjacency

print(f"Building {ADJACENCY} adjacency network...")

if ADJACENCY not in {"rook", "queen"}:
    raise ValueError("ADJACENCY must be 'rook' or 'queen'")

# Spatial index prevents checking every county against every other county
sindex = geo.sindex

edge_records = []

geometries = geo.geometry.to_numpy()
fips_values = geo["fips"].to_numpy()

for i, geometry in enumerate(geometries):

    # Bounding-box candidates
    candidates = sindex.query(
        geometry,
        predicate="intersects",
    )

    for j in candidates:

        j = int(j)

        # Avoid self-links and duplicate undirected edges
        if j <= i:
            continue

        other = geometries[j]

        # Geographic adjacency requires touching boundaries
            # Not just overlapping bounding boxes
        if not geometry.touches(other):
            continue

        shared = geometry.boundary.intersection(
            other.boundary
        )

        shared_length_m = float(shared.length)

        if ADJACENCY == "rook":
            if shared_length_m < MIN_SHARED_BORDER_M:
                continue

        a = str(fips_values[i])
        b = str(fips_values[j])

        source, target = sorted((a, b))

        edge_records.append({
            "source_fips": source,
            "target_fips": target,
            "shared_border_km": shared_length_m / 1000,
        })

edges = pd.DataFrame(
    edge_records,
    columns=[
        "source_fips",
        "target_fips",
        "shared_border_km",
    ],
)

edges = edges.drop_duplicates(
    ["source_fips", "target_fips"]
)

edges = edges.sort_values(
    ["source_fips", "target_fips"]
).reset_index(drop=True)


# Geographic network statistics

degree_counts = pd.concat(
    [
        edges["source_fips"],
        edges["target_fips"],
    ],
    ignore_index=True,
).value_counts()

counties["degree"] = (
    counties["fips"]
    .map(degree_counts)
    .fillna(0)
    .astype(int)
)


# Export everything for use in notebook

county_columns = [
    "fips",
    "state_fips",
    "state",
    "county",
    "official_name",
    "latitude",
    "longitude",
    "degree",
    *POPULATION_COLUMNS,
]

counties[county_columns].to_csv(
    OUT / "counties.csv",
    index=False,
)

edges.to_csv(
    OUT / "edges.csv",
    index=False,
)

# Save geographic boundaries for maps and visualization
export_geo = counties[
    ["fips", "official_name", "geometry"]
].copy()

export_geo = gpd.GeoDataFrame(
    export_geo,
    geometry="geometry",
    crs=tiger.crs,
)

export_geo.to_crs("EPSG:4326").to_file(
    OUT / "county_network.geojson",
    driver="GeoJSON",
)

# An explicit diagnostics file for duplicate keys.
pd.DataFrame(
    columns=["source", "match_key", "reason"]
).to_csv(
    OUT / "ambiguous_matches.csv",
    index=False,
)


# Validation debugging

node_count = len(counties)
edge_count = len(edges)

matched_count = counties[
    "population_2025"
].notna().sum()

missing_population = (
    node_count - matched_count
)

isolated_count = (
    counties["degree"] == 0
).sum()

print()
print("=" * 55)
print("COUNTY NETWORK BUILD COMPLETE")
print("=" * 55)

print(f"Nodes:                {node_count:,}")
print(f"Border edges:         {edge_count:,}")
print(f"Matched populations:  {matched_count:,}")
print(f"Missing populations:  {missing_population:,}")
print(f"Isolated nodes:       {isolated_count:,}")

print()
print("Outputs:")
print(f"  {OUT / 'counties.csv'}")
print(f"  {OUT / 'edges.csv'}")
print(f"  {OUT / 'county_network.geojson'}")
print(f"  {OUT / 'unmatched_counties.csv'}")

if missing_population:
    print()
    print(
        "WARNING: Some geographic units have no matched "
        "population. Review diagnostics before simulation."
    )