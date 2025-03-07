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
    orders = pd.read_csv("orders_dataset.csv")
    customers = pd.read_csv("customers_dataset.csv")
    order_items = pd.read_csv("order_items_dataset.csv")
    products = pd.read_csv("products_dataset.csv")
    category_translations = pd.read_csv("product_category_name_translation.csv")
    return orders, customers, order_items, products, category_translations

orders, customers, order_items, products, category_translations = load_data()

st.write("Data Loaded Successfully! Here's a preview:")
st.dataframe(orders.head())

# Data Cleaning
orders = orders.drop(['order_approved_at', 'order_estimated_delivery_date', 'order_delivered_carrier_date', 'order_delivered_customer_date'], axis=1)
products = products.drop(['product_name_lenght', 'product_description_lenght', 'product_photos_qty', 'product_weight_g', 'product_length_cm', 'product_height_cm', 'product_height_cm'], axis=1)
order_items = order_items.drop(['seller_id', 'freight_value', 'shipping_limit_date'], axis=1)
orders["order_purchase_timestamp"] = pd.to_datetime(orders["order_purchase_timestamp"])
products.fillna(value="other", inplace=True)

# Merging Data
sales_df = orders.merge(order_items, on="order_id").merge(customers, on="customer_id")
sales_df = sales_df[sales_df["order_status"] == "delivered"]

# Sales Trend
sales_df["order_purchase_month"] = sales_df["order_purchase_timestamp"].dt.to_period("M")
sales_trend = sales_df.groupby(["customer_state", "order_purchase_month"])['price'].sum().reset_index()

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

# Visualization: Sales by State
st.subheader("Product Sales Trend by State")
fig, ax = plt.subplots(figsize=(12, 6))
sales_df.groupby("customer_state")["order_id"].count().sort_values().plot(kind='barh', ax=ax)
plt.xlabel("Number of Orders")
plt.ylabel("State")
plt.title("Product Sales Trend by State")
st.pyplot(fig)

# Sales Trend Over Time
st.subheader("Sales Trend Over Time")
sales_trend['order_purchase_month'] = sales_trend['order_purchase_month'].astype(str)
fig, ax = plt.subplots(figsize=(12, 6))
sns.lineplot(data=sales_trend, x="order_purchase_month", y="price", hue="customer_state", ax=ax)
plt.xticks(rotation=45)
plt.title("Product Sales Trend by State")
plt.xlabel("Month")
plt.ylabel("Total Sales")
st.pyplot(fig)

# Heatmap of Category Pairs
st.subheader("Frequently Purchased Product Category Pairs")
top_products = filtered_pairs_df.head(20)["Category Pair"].tolist()
heatmap_data = pd.DataFrame(0, index=list(set([p[0] for p in top_products] + [p[1] for p in top_products])),
                            columns=list(set([p[0] for p in top_products] + [p[1] for p in top_products])))

for (prod1, prod2), count in category_pairs_counter.items():
    if prod1 in heatmap_data.index and prod2 in heatmap_data.columns:
        heatmap_data.at[prod1, prod2] = count
        heatmap_data.at[prod2, prod1] = count

fig, ax = plt.subplots(figsize=(10, 8))
sns.heatmap(heatmap_data, annot=True, fmt="d", cmap="Blues", ax=ax)
plt.title("Heatmap of Frequently Purchased Product Category Pairs")
st.pyplot(fig)

# Top 10 Frequently Bought Together Pairs
st.subheader("Top 10 Frequently Bought Together Product Pairs")
pair_labels = [f"{pair[0]} & {pair[1]}" for pair in filtered_pairs_df["Category Pair"].head(10)]
fig, ax = plt.subplots(figsize=(12, 6))
sns.barplot(x=filtered_pairs_df["Count"].head(10), y=pair_labels, palette="Blues_r", ax=ax)
plt.xlabel("Count")
plt.ylabel("Product Pair")
plt.title("Top 10 Frequently Purchased Product Category Pairs")
st.pyplot(fig)
