import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from collections import Counter

# Title
st.title("E-Commerce Sales Analysis")

# Load datasets
@st.cache_data  # Cache to optimize performance
def load_data():
    orders = pd.read_csv("data/orders_dataset.csv")
    customers = pd.read_csv("data/customers_dataset.csv")
    order_items = pd.read_csv("data/order_items_dataset.csv")
    products = pd.read_csv("data/products_dataset.csv")
    category_translations = pd.read_csv("data/product_category_name_translation.csv")
    return orders, customers, order_items, products, category_translations

orders, customers, order_items, products, category_translations = load_data()

st.write("Data Loaded Successfully! Here's a preview:")

# Sidebar Filters
st.sidebar.header("Filters")

# Date range filter
min_date = pd.to_datetime("2016-01-01")
max_date = pd.to_datetime("2018-12-31")
date_range = st.sidebar.date_input("Select Date Range:", [min_date, max_date], min_value=min_date, max_value=max_date)

# Category filter
all_categories = order_items.merge(products, on="product_id").merge(category_translations, on="product_category_name", how="left")["product_category_name_english"].dropna().unique().tolist()
selected_category1 = st.sidebar.selectbox("Select First Product Category:", all_categories)
selected_category2 = st.sidebar.selectbox("Select Second Product Category:", all_categories)

# Data Cleaning
orders = orders.drop(['order_approved_at', 'order_estimated_delivery_date', 'order_delivered_carrier_date', 'order_delivered_customer_date'], axis=1)
products = products.drop(['product_name_lenght', 'product_description_lenght', 'product_photos_qty', 'product_weight_g', 'product_length_cm', 'product_height_cm', 'product_height_cm'], axis=1)
order_items = order_items.drop(['seller_id', 'freight_value', 'shipping_limit_date'], axis=1)
orders["order_purchase_timestamp"] = pd.to_datetime(orders["order_purchase_timestamp"])
products.fillna(value="other", inplace=True)

# Merging Data
sales_df = orders.merge(order_items, on="order_id").merge(customers, on="customer_id")
sales_df = sales_df[sales_df["order_status"] == "delivered"]

# Apply date filter
sales_df = sales_df[(sales_df["order_purchase_timestamp"] >= pd.to_datetime(date_range[0])) & (sales_df["order_purchase_timestamp"] <= pd.to_datetime(date_range[1]))]

# Visualization: Sales by State
st.subheader("All Time Product Sales Trend by State")
fig, ax = plt.subplots(figsize=(12, 6))
sales_df.groupby("customer_state")["order_id"].count().sort_values().plot(kind='barh', ax=ax)
plt.xlabel("Number of Orders")
plt.ylabel("State")
plt.title("Product Sales Trend by State")
st.pyplot(fig)

# Sales Trend Over Time
st.subheader("Sales Trend by State")
state_list = sales_df["customer_state"].unique().tolist()

selected_state = st.selectbox("Select a State:", ["All"] + state_list)

if selected_state != "All":
    sales_trend = sales_df[sales_df["customer_state"] == selected_state].groupby("order_purchase_timestamp")['price'].sum().reset_index()
else:
    sales_trend = sales_df.groupby("order_purchase_timestamp")['price'].sum().reset_index()

fig, ax = plt.subplots(figsize=(12, 6))
sns.lineplot(data=sales_trend, x="order_purchase_timestamp", y="price", ax=ax)
plt.xticks(rotation=45)
plt.title(f"Sales Trend - {selected_state}")
plt.xlabel("Date")
plt.ylabel("Total Sales")
st.pyplot(fig)

# Heatmap of Category Pairs
if selected_category1 and selected_category2:
    st.subheader(f"Heatmap of {selected_category1} and {selected_category2}")
    category_pairs_counter = Counter()
    for order_products in order_items.merge(products, on="product_id").merge(category_translations, on="product_category_name", how="left").groupby("order_id")["product_category_name_english"].apply(list):
        unique_categories = set(order_products)
        if selected_category1 in unique_categories and selected_category2 in unique_categories:
            category_pairs_counter[(selected_category1, selected_category2)] += 1
    
    heatmap_data = pd.DataFrame([[category_pairs_counter.get((selected_category1, selected_category2), 0)]], 
                                index=[selected_category1], 
                                columns=[selected_category2])
    
    fig, ax = plt.subplots(figsize=(5, 5))
    sns.heatmap(heatmap_data, annot=True, fmt="d", cmap="Blues", ax=ax)
    plt.title(f"Heatmap of {selected_category1} and {selected_category2}")
    st.pyplot(fig)

# Frequently Bought Together Analysis
order_items_df = order_items.merge(products, on="product_id").merge(category_translations, on="product_category_name", how="left")
basket = order_items_df.groupby("order_id")["product_category_name_english"].apply(list)

pairs = Counter()
for products in basket:
    for i in range(len(products)):
        for j in range(i+1, len(products)):
            pairs[(products[i], products[j])] += 1

pairs_df = pd.DataFrame(pairs.items(), columns=["Product Pair", "Count"]).sort_values(by="Count", ascending=False)

category_pairs_counter = Counter()
for order_products in order_items_df.groupby("order_id")["product_category_name_english"].apply(list):
    unique_categories = list(set(order_products))
    for i in range(len(unique_categories)):
        for j in range(i + 1, len(unique_categories)):
            category_pairs_counter[(unique_categories[i], unique_categories[j])] += 1

filtered_pairs_df = pd.DataFrame(category_pairs_counter.items(), columns=["Category Pair", "Count"]).sort_values(by="Count", ascending=False)

# Top 10 Frequently Bought Together Pairs
st.subheader("Top 10 Frequently Bought Together Product Pairs")

# Ensure DataFrame is not empty
if not filtered_pairs_df.empty:
    pair_labels = [f"{pair[0]} & {pair[1]}" for pair in filtered_pairs_df["Category Pair"].head(10)]

    # Plot
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(x=filtered_pairs_df["Count"].head(10), y=pair_labels, palette="Blues_r", ax=ax)
    plt.xlabel("Count")
    plt.ylabel("Product Pair")
    plt.title(f"Top 10 Frequently Purchased Product Category Pairs")
    st.pyplot(fig)
else:
    st.warning("No data available to display frequently bought together pairs.")

