This project demonstrates a comprehensive methodology for developing an objective, data driven talent matching and profiling system. It converts complex behavioral and psychometric data into actionable business intelligence using a three stage process: Success Formula discovery, parameterized SQL logic, and a dynamic AI powered web application.

The core goal is to enable Human Resources (HR) and managerial stakeholders to define the ideal profile of high performing employees (Rating 5 from year 2025 data) and instantly benchmark the entire employee pool against that standard.

# Project Stages

## Stage 1: Success Formula Definition

The initial objective was to perform retrospective analysis on the 2025 performance data to identify the distinguishing characteristics of high performing employees (Rating 5). This involved examining various data pillars:

- Competency Pillars: Evaluating performance across core skills (e.g., Quality Delivery, Strategic Impact).

- Psychometric Profiles: Analyzing assessment results (e.g.,IQ, GTQ, DISC, PAPI scores).

- Contextual Factors: Including organizational context (e.g., Grade, Years of Service).

The output of this stage is the Success Formula, a weighted framework that determines how each Talent Variable (TV) contributes to overall performance through Talent Group Variables (TGV).

## Stage 2: Operationalizing Logic in Parameterized SQL

This stage focuses on turning the qualitative Success Formula into robust, dynamic SQL queries. The logic is implemented using multiple Common Table Expressions (CTEs) to calculate employee fit scores against a dynamically set benchmark.

The core matching algorithm is:

- Baseline Aggregation: Computing the median/mode of all TV scores from the selected high performing benchmark employees.

- TV Match Rate: Calculating the ratio of a candidate's score against the benchmark's score (e.g., Candidate Score / Baseline Score).

- TGV and Final Match Rate: Aggregating TV matches into TGV scores, and applying user specified weights to TGVs to determine the Final Match Rate.

The resulting SQL script (query.sql) is fully parameterized, allowing it to be executed with new inputs (Role, Level, Benchmark IDs) at runtime.

## Stage 3: AI Powered Dashboard Deployment

#### 🚀 Live Dashboard
[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://talentappdashboard.streamlit.app/)

The final step is the creation of an AI powered, interactive web dashboard using Streamlit. This dashboard is designed to provide actionable insight at runtime, without requiring static pre baked data.

Key Features of the Dashboard:

- Provide clear, interactive visuals for each new input/job vacancy:

- Match rate distributions

- Top strengths and gaps across TGVs

- Benchmark vs candidate comparisons (radar, heatmap, bar plots)

- Summary insights explaining why certain employees rank highest

- Dynamic Inputs: Users define the role (Role Name, Job Level) and select benchmark employee IDs directly through the interface.

- AI Generated Profile: The application connects to an external LLM to dynamically generate the Job Requirements, Description, and Key Competencies based on the user's input Role Purpose.

    Note on LLM Models: This feature utilizes the **OpenRouter API** to access free tier models, specifically **TNG: DeepSeek R1T2 Chimera and MiniMax: MiniMax M2**. Due to the nature of these free tier models, the quality and structure of the generated output may occasionally be sub optimal or require a retry.

- Parameterized Calculation: The dashboard executes the parameterized SQL script in real time when new inputs are submitted.

- Actionable Visualizations: Presents results through a Ranked Talent List, Match Rate Distribution, TGV Radar Charts (Benchmark comparison), and Detailed TV Heatmaps (individual strengths and gaps).