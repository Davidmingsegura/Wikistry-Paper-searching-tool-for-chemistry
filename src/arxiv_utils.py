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

summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6", device=-1)

def fetch_arxiv(query, max_results=5):
    """Fetch articles from arXiv using flexible query syntax."""
    base_url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": f"all:{query}", 
        "start": 0,
        "max_results": max_results
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching ArXiv articles: {e}")
        return None


def parse_arxiv_response(xml_response):
    """Parse the arXiv XML response into a standardized list of articles."""
    try:
        root = ET.fromstring(xml_response)  # Parse the XML
    except ET.ParseError as e:
        print(f"Error parsing ArXiv XML: {e}")
        return []

    namespace = {"atom": "http://www.w3.org/2005/Atom"}

    articles = []
    for entry in root.findall("atom:entry", namespace):
        title = entry.find("atom:title", namespace).text.strip() if entry.find("atom:title", namespace) is not None else "No title"
        summary = entry.find("atom:summary", namespace).text.strip() if entry.find("atom:summary", namespace) is not None else "No abstract"
        link = entry.find("atom:id", namespace).text.strip() if entry.find("atom:id", namespace) is not None else "No link"

        authors = []
        for author in entry.findall("atom:author", namespace):
            name = author.find("atom:name", namespace).text.strip() if author.find("atom:name", namespace) is not None else "Unknown Author"
            authors.append(name)

        articles.append({
            "title": title,
            "abstract": summary,
            "link": link,
            "authors": ", ".join(authors)
        })

    return articles
def summarize_text(text):
    """Summarize the given text, dynamically adjusting max_length."""
    text_length = len(text.split())
    max_length = min(100, text_length + 10)  
    return summarizer(text, max_length=max_length, min_length=5, do_sample=False)[0]['summary_text']


def search_and_summarize(query, max_results=5):
    """Search and summarize articles from arxiv"""
    arxiv_data = fetch_arxiv(query, max_results=max_results)
    arxiv_articles = parse_arxiv_response(arxiv_data) if arxiv_data else []

    all_articles = acs_articles

    for article in all_articles:
        if "abstract" in article and article["abstract"] != "No abstract":
            article["summary"] = summarize_text(article["abstract"])
        else:
            article["summary"] = "No abstract available for summarization."

    return all_articles

fetch_arxiv_tool = Tool(
    name="FetchArxiv",
    func=lambda query: parse_arxiv_response(fetch_arxiv(query)),
    description=(
        "Fetches articles from arXiv based on a query. "
        "Returns a list of articles with titles, abstracts, and links."
    )
)

summarize_tool = Tool(
    name="SummarizeText",
    func=summarize_text,
    description=(
        "Summarizes a given text using a pre-trained summarization model. "
        "The input text should be a single abstract or article content."
    )
)
load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)  
agent = initialize_agent(
    tools=[fetch_arxiv_tool, summarize_tool],
    llm=llm,
    agent="zero-shot-react-description",
    verbose=True
)
