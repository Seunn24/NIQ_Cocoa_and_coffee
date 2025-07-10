import pandas as pd
import streamlit as st

# First loading the extracted dataset belonging to coffee and cocoa
@st.cache_data
def load_data(path):
    return pd.read_excel(path)

df = load_data('NIQ_coffee_cocoa.xlsx')


# Cleaning the textual feilds 
df['description_clean'] = df['Description'].astype(str).str.lower()
df['ingredients_clean'] = df['Ingredients'].astype(str).str.lower()


commodity_mapping = {
    # Coffee
    "instant coffee": "210112",
    "coffee extract": "210112",
    "coffee":         "0901",
    # Cocoa
    "cocoa beans":  "180100",
    "cocoa paste":  "180300",
    "cocoa mass":   "180300",
    "cocoa butter": "180400",
    "cocoa powder": "180510",
    "chocolate":    "1806",
}

def assign_code(text, mapping):
    for kw, code in mapping.items():
        if kw in text:
            return code
    return None

# FLAG BY NAME, AND USE THE EXISTING commodity_code AS "INGREDIENT-BASED"
df['code_by_name']       = df['description_clean'].apply(lambda t: assign_code(t, commodity_mapping))
df['code_by_ingredient'] = df['commodity_code']  # this is already in my extracted file


# BUILD STORY 1 & STORY 2 SUMMARIES
story1 = df[df['code_by_name'].notna()]
story2 = df[df['code_by_ingredient'].notna()]

story1_summary = (
    story1
    .pivot_table(index='code_by_name',
                 columns='Subscriber Code',
                 aggfunc='size',
                 fill_value=0)
    .reset_index()
)

story2_summary = (
    story2
    .pivot_table(index='code_by_ingredient',
                 columns='Subscriber Code',
                 aggfunc='size',
                 fill_value=0)
    .reset_index()
)

soy_kw    = ['soy', 'soya', 'soybean']
rubber_kw = ['rubber']

df['contains_soy']    = df['ingredients_clean'].apply(lambda t: any(k in t for k in soy_kw))
df['contains_rubber'] = df['ingredients_clean'].apply(lambda t: any(k in t for k in rubber_kw))


# STREAMLIT UI
st.title("EUDR Exposure Dashboard (Coffee & Cocoa)")

# Sidebar filters
subs = st.sidebar.multiselect(
    "Subscriber Code",
    options=df['Subscriber Code'].unique(),
    default=df['Subscriber Code'].unique()
)

valid_subs = [sub for sub in subs if sub in df['Subscriber Code'].values]

if not valid_subs:
    st.sidebar.warning("No valid Subscriber Codes selected.")

story = st.sidebar.radio(
    "Select Story",
    ["1. Name-based Exposure",
     "2. Ingredient-based Exposure",
     "3. Additional Flags"]
)

# Apply filter to the main dataframe
df_filtered = df[df['Subscriber Code'].isin(valid_subs)]

# Rebuild story summaries based on the filtered dataset
story1 = df_filtered[df_filtered['code_by_name'].notna()]
story2 = df_filtered[df_filtered['code_by_ingredient'].notna()]

story1_summary = (
    story1
    .pivot_table(index='code_by_name',
                 columns='Subscriber Code',
                 aggfunc='size',
                 fill_value=0)
    .reset_index()
)

story2_summary = (
    story2
    .pivot_table(index='code_by_ingredient',
                 columns='Subscriber Code',
                 aggfunc='size',
                 fill_value=0)
    .reset_index()
)

# Handle filtering of the summary based on the valid Subscriber Codes
if story == "1. Name-based Exposure":
    st.header("Story 1: In-Scope by Product Name")
    st.dataframe(story1_summary)

    # Only include valid subscriber codes that exist in the story1_summary columns
    valid_columns = [col for col in valid_subs if col in story1_summary.columns]
    
    # Filter the summary and plot the data
    story1_summary_filtered = story1_summary[['code_by_name'] + valid_columns]
    st.bar_chart(story1_summary_filtered.set_index('code_by_name')[valid_columns])

elif story == "2. Ingredient-based Exposure":
    st.header("Story 2: In-Scope by Ingredients")
    st.dataframe(story2_summary)

    # Filter for only valid Subscriber Codes in the summary
    valid_columns = [col for col in valid_subs if col in story2_summary.columns]
    story2_summary_filtered = story2_summary[['code_by_ingredient'] + valid_columns]
    st.bar_chart(story2_summary_filtered.set_index('code_by_ingredient')[valid_columns])

else:
    st.header("Additional Flags")
    flags = df_filtered[['contains_soy', 'contains_rubber']].sum().rename('Count')
    st.table(flags)

if st.sidebar.checkbox("Show raw data"):
    st.subheader("Raw Data")
    st.dataframe(df_filtered)
