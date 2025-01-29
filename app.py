import requests
from transformers import pipeline
from langchain.agents import initialize_agent
from langchain.tools import Tool
import xml.etree.ElementTree as ET
import streamlit as st
from langchain.agents import initialize_agent
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI 
from langchain_community.llms import OpenAI
import xml.etree.ElementTree as ET
from arxiv_utils import (
    fetch_arxiv, 
    parse_arxiv_response, 
    fetch_arxiv_tool, 
    summarize_tool, 
    summarize_text, 
    search_and_summarize
)

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6", device=-1)

st.title("🔬 Chemistry Paper Search Tool 🔬")

query = st.text_input("Enter your research topic:", "Machine Learning for Chemistry")
source = st.radio("Select Source:", ("arXiv", "ACS (Experimental)"))

if st.button("Search"):
    st.write("🔎 **Searching for:**", query)

    if source == "arXiv":
        articles = parse_arxiv_response(fetch_arxiv(query, max_results=5))
    elif source == "ACS (Experimental)":
        articles = fetch_acs_articles_selenium(query, max_results=5)
    
    if articles:
        for article in articles:

            st.write(f"### {article['title']}", unsafe_allow_html=True)
            st.markdown(f"[Read more]({article['link']})")

            if article["abstract"] and article["abstract"] != "No abstract":
                input_length = len(article["abstract"].split())
                max_len = min(100, input_length + 10)  
                min_len = max(20, int(max_len * 0.5))  

                if min_len >= max_len:
                    min_len = max_len - 1  

                try:
                    summary_result = summarizer(
                        article["abstract"],
                        max_length=max_len,
                        min_length=min_len,
                        do_sample=False,
                    )
                    article["summary"] = summary_result[0]["summary_text"]
                except Exception as e:
                    st.error(f"Error summarizing article: {e}")
                    article["summary"] = "Summary generation failed."
            else:
                article["summary"] = "No abstract available for summarization."

            st.write(f"**Summary:** {article['summary']}")
            st.markdown("---")
