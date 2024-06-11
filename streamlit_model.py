import pandas as pd
import numpy as np
import quantstats as qs
import streamlit as st
bist100returns=pd.read_csv("bist100returns.csv")
st.set_page_config(page_title="AI Trading Model Takip Sayfası")
fig = qs.plots.snapshot(bist100returns,show=False)
st.pyplot(fig)

