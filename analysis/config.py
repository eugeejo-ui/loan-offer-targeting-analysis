"""Paths and column names shared by every analysis module and script."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE_XES = Path(r"C:\sap-btm-financial-prospecting\data\bpi2017\BPI Challenge 2017.xes")
CACHE_PARQUET = ROOT / "data" / "bpi2017_events.parquet"
OUT_DIR = ROOT / "outputs"

CASE = "case:concept:name"
ACT = "concept:name"
TS = "time:timestamp"
LIFECYCLE = "lifecycle:transition"
RESOURCE = "org:resource"
ORIGIN = "EventOrigin"
EVENT_ID = "EventID"
OFFER_ID = "OfferID"
ACTION = "Action"

END_LABELS = {"A_Pending": "success", "A_Denied": "denied", "A_Cancelled": "cancelled"}
INTAKE_ATTRS = ["case:RequestedAmount", "case:LoanGoal", "case:ApplicationType"]
OFFER_ATTRS = [
    "OfferedAmount", "CreditScore", "MonthlyCost", "NumberOfTerms",
    "FirstWithdrawalAmount", "Selected", "Accepted",
]
BOOL_ATTRS = ["Selected", "Accepted"]
SYSTEM_RESOURCE = "User_1"
