"""Setup script for the Business Advisor system."""

from setuptools import setup, find_packages

setup(
    name="business-advisor",
    version="1.0.0",
    description="A LangGraph-based AI agent system for analyzing business opportunities",
    author="AI Business Analyst",
    packages=find_packages(),
    install_requires=[
        "langgraph>=0.2.0",
        "langchain-groq>=0.2.0",
        "serpapi>=0.1.5",
        "vaderSentiment>=3.3.2",
        "pandas>=2.0.0",
        "geopy>=2.4.0",
        "python-dotenv>=1.0.0",
        "groq>=0.5.0",
        "requests>=2.31.0",
        "typing_extensions>=4.8.0"
    ],
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)