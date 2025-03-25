import streamlit as st
import pandas as pd
from math import sqrt
from fractions import Fraction
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# --- Utility Functions ---
def round_to_nearest(value, precision):
    if precision == 0:
        return round(value, 4)
    return round(round(value / precision) * precision, 4)

def format_fraction(value, precision):
    whole = int(value)
    frac = round(value - whole, 4)
    if frac == 0:
        return f"{whole}\""
    fraction = Fraction(frac).limit_denominator(int(1 / precision))
    return f"{whole} {fraction.numerator}/{fraction.denominator}\"" if whole else f"{fraction.numerator}/{fraction.denominator}\""

def display_length(value, rounding, display):
    if rounding == "No Rounding":
        return f"{round(value, 4)}\"" if display == "Decimal" else format_fraction(value, 1/16)
    step = {
        "Nearest 1/16\"": 1/16,
        "Nearest 1/8\"": 1/8,
        "Nearest 1/4\"": 1/4,
        "Nearest 1/2\"": 1/2
    }[rounding]
    rounded = round_to_nearest(value, step)
    return f"{rounded}\"" if display == "Decimal" else format_fraction(rounded, step)

# --- Sidebar Inputs ---
st.sidebar.header("Input Parameters")
projection = st.sidebar.number_input("Projection (in)", value=48.0)
drop = st.sidebar.number_input("Drop / Height (in)", value=55.2)
clip_setback = st.sidebar.number_input("Tie-Back Clip Center Setback (in)", value=10.0)
quantity = st.sidebar.number_input("Quantity of Arms", value=1, step=1)

st.sidebar.header("Display Settings")
rounding_option = st.sidebar.selectbox("Rounding Precision", ["No Rounding", "Nearest 1/16\"", "Nearest 1/8\"", "Nearest 1/4\"", "Nearest 1/2\""], index=1)
display_format = st.sidebar.selectbox("Display Format", ["Decimal", "Fraction"], index=1)

# --- Advanced Geometry Offsets ---
edit_geometry_offsets = st.sidebar.checkbox("Edit Arm Geometry Offsets", value=False)
if "wall_axis" not in st.session_state:
    st.session_state["wall_axis"] = 1.688
if "structure_axis" not in st.session_state:
    st.session_state["structure_axis"] = 1.438

if edit_geometry_offsets:
    st.session_state["wall_axis"] = st.sidebar.number_input("Wall-to-Clip Axis Offset (in)", value=st.session_state["wall_axis"])
    st.session_state["structure_axis"] = st.sidebar.number_input("Structure-to-Axis Offset (in)", value=st.session_state["structure_axis"])

wall_axis = st.session_state["wall_axis"]
structure_axis = st.session_state["structure_axis"]

# --- Reveal Settings ---
edit_reveal_settings = st.sidebar.checkbox("Edit Reveal Settings", value=False)
if "clevis_reveal" not in st.session_state:
    st.session_state["clevis_reveal"] = 1.5
if "tb_reveal" not in st.session_state:
    st.session_state["tb_reveal"] = 3.5

if edit_reveal_settings:
    st.session_state["clevis_reveal"] = st.sidebar.number_input("Clevis-Side Reveal (in)", value=st.session_state["clevis_reveal"])
    st.session_state["tb_reveal"] = st.sidebar.number_input("Turnbuckle-Side Reveal (in)", value=st.session_state["tb_reveal"])

clevis_reveal = st.session_state["clevis_reveal"]
tb_reveal = st.session_state["tb_reveal"]

# --- Hardware Specs ---
with st.sidebar.expander("Hardware Specifications"):
    clevis_1_model = st.text_input("Structure-Side Clevis Model", value="CL25300-0531")
    clevis_1_len = st.number_input("Structure-Side Clevis Length (in)", value=4.0)
    turnbuckle_model = st.text_input("Turnbuckle Model", value="TB0900-0001")
    turnbuckle_len = st.number_input("Turnbuckle Length (in)", value=4.0)
    clevis_2_model = st.text_input("Wall-Side Clevis Model", value="CL25300-0531")
    clevis_2_len = st.number_input("Wall-Side Clevis Length (in)", value=4.0)

# --- Calculations ---
ctc_total = clevis_1_len + turnbuckle_len + clevis_2_len
horizontal = projection - clip_setback - wall_axis
vertical = drop - structure_axis
p2p = sqrt(horizontal ** 2 + vertical ** 2)
n = p2p - ctc_total
rod_length = n / 2
threaded_rod_length = clevis_reveal + tb_reveal
tube_length = rod_length - threaded_rod_length

# --- Output Table ---
data = []

# Arm components summary (for all arms)
data.extend([
    ["--- Arm Components ---", "", ""],
    ["Number of Arms", str(quantity), "Total arms to fabricate"],
    ["Tube Length", display_length(tube_length, rounding_option, display_format), "cut to spec"],
    ["Rod Length", display_length(rod_length, rounding_option, display_format), "each side of turnbuckle"],
    ["Threaded Rod Length", display_length(threaded_rod_length, rounding_option, display_format), "welded in tube"]
])

# Global values
data.extend([
    ["", "", ""],
    ["--- Global Parameters ---", "", ""],
    ["Clevis-Side Reveal", display_length(clevis_reveal, rounding_option, display_format), "used in rod calc"],
    ["Turnbuckle-Side Reveal", display_length(tb_reveal, rounding_option, display_format), "used in rod calc"],
    ["P2P Distance", display_length(p2p, rounding_option, display_format), "clevis to clevis"]
])

# Hardware section
data.extend([
    ["", "", ""],
    ["--- Hardware Specs ---", "", ""],
    ["Structure-Side Clevis", display_length(clevis_1_len, rounding_option, display_format), f"{clevis_1_model} (tie-back clip end)"],
    ["Turnbuckle", display_length(turnbuckle_len, rounding_option, display_format), f"{turnbuckle_model} (center connector)"],
    ["Wall-Side Clevis", display_length(clevis_2_len, rounding_option, display_format), f"{clevis_2_model} (wall plate end)"]
])

# --- Display Table ---
df = pd.DataFrame(data, columns=["Component", "Length", "Model / Notes"]).astype(str)
st.title("Clevis-Rod-Turnbuckle (CRT) Arm Calculator")
st.dataframe(df, use_container_width=True)

csv = df.to_csv(index=False).encode('utf-8')
st.download_button("Download CSV", data=csv, file_name="crt_arm_output.csv", mime="text/csv")
