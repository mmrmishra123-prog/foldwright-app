# Foldwright

An AI research assistant for protein engineering.

Foldwright allows users to enter a protein engineering goal in plain English, such as "make GFP brighter," and receive ranked mutation suggestions with explanations and supporting sources where available.

## Features

- Interprets protein engineering goals from natural language
- Ranks candidate mutations using ESM-2, BLOSUM62, and conservation scores
- Uses a Neo4j knowledge graph to retrieve information about mutations and documented effects
- Generates explanations for each suggested mutation
- Includes supporting sources where available
- Provides an interactive interface built with Streamlit

## How It Works

1. The user enters a protein engineering goal.
2. The goal is interpreted to identify the desired effect.
3. Candidate mutations are retrieved and ranked based on mutation scores.
4. Relevant biological information is retrieved from a Neo4j knowledge graph.
5. The app generates explanations for the top-ranked mutations.

## Tech Stack

- Python
- Streamlit
- Neo4j
- Google Gemini API
- ESM-2
- BLOSUM62

## Try Foldwright

[Try the live app here](https://foldwright-app-auvmrfwfgjd5ox7z2yfhnl.streamlit.app/)

## Running Locally

Clone the repository:

```bash
git clone https://github.com/mmrmishra123-prog/foldwright-app.git
cd foldwright-app
