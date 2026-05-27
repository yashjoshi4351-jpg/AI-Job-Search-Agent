#==========
# API KEYS
# ==========

from dotenv import load_dotenv
import os
load_dotenv()

Job_API_Key = os.getenv("adzuna")
GROQ_API_KEY  = os.getenv("groq")
API_ID = os.getenv("adzuna_id")
INSIGHTS = os.getenv("company_insights")


# ================
# USED LIBRARIES
# ================

from langchain_groq import ChatGroq
from typing import TypedDict,List,Optional
from langgraph.graph import StateGraph, END
import requests
import json
import pdfplumber

# ==============
# PLANNERSTATE
# ==============

class PlannerState(TypedDict):
    # =========================
    # 1. RESUME DATA
    # =========================
    resume_file_path: Optional[str]
    resume_text: Optional[str]

    # =========================
    # 2. PARSED RESUME DATA
    # =========================
    name: Optional[str]
    email: Optional[str]
    location: Optional[str]
    skills: Optional[List[str]]
    projects: Optional[List[str]]
    experience: Optional[List[str]]
    education: Optional[List[str]]
    resume_date: Optional[str]


    # =========================
    # 3. INFERRED PROFILE (AUTO-GENERATED)
    # =========================
    inferred_role: Optional[str]    # e.g. "Data Analyst"


    # =========================
    # 4. JOB SEARCH DATA AND COMPANY INSIGHTS DATA
    # =========================
    job_results: Optional[List[dict]]
    company_insights: Optional[List[dict]]


    # =========================
    # 5. RESUME OPTIMIZATION
    # =========================
    optimized_resume_text: Optional[str]

    itinerary:Optional[str]

    errors: Optional[str]


# ========
# LLM
# ========

llm = ChatGroq(
    model = "llama-3.3-70b-versatile",
    api_key = GROQ_API_KEY,
    temperature= 0.4,
    max_tokens = 4000
)



# =================================
# AGENTS
# =================================

# 1.CONVERT PDF->TEXT

def textconverter(state: PlannerState):
    PDF = state["resume_file_path"]


    with pdfplumber.open(PDF) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text()

    return{
        **state,
        "resume_text": text
    }



# 2.INPUT AGENT



def input_parser_agent(state: PlannerState):
    """LLM extracts details and converts cities to IATA codes."""
    last_message = state["resume_text"]

    prompt = f"""
    Extract resume details from this message: "{last_message}"


    Return ONLY a JSON object:
    {{
        name: str
        email: str
        location: str   ex. India, USA
        skills: str
        projects: str
        experience: str
        education: str
        date :str      format: YYYY-MM-DD
    }}
    If unknown, use null.
    """

    response = llm.invoke(prompt)
    content = response.content.strip().replace("```json", "").replace("```", "")
    extracted_data = json.loads(content)

    return {
        **state,
        "name": extracted_data.get("name"),
        "email": extracted_data.get("email"),
        "location": extracted_data.get("location"),
        "skills": extracted_data.get("skills"),
        "projects": extracted_data.get("projects"),
        "experience": extracted_data.get("experience"),
        "education": extracted_data.get("education"),
        "resume_date": extracted_data.get("date")
    }


# 3. AUTO ROLE GENERATED AGENT


def role_inference_agent(state: PlannerState):

    skills = state.get("skills")
    projects = state.get("projects")

    prompt = f"""
    Analyze the candidate profile.

    Skills:
    {skills}

    Projects:
    {projects}


    Predict the MOST suitable job role.

    Examples:
    - Data Analyst
    - Backend Developer
    - AI Engineer
    - Frontend Developer

    Return ONLY role name.
    """

    response = llm.invoke(prompt)

    return {
        **state,
        "inferred_role": response.content.strip()
    }

# 4. JOB SEARCH AGENT


def job_search(state: PlannerState):

    what = state["inferred_role"]
    where = state["location"]

    try:

        url = "https://api.adzuna.com/v1/api/jobs/in/search/1"

        params = {
            "app_id": API_ID,
            "app_key": Job_API_Key,
            "what": what,
            "where": where,
            "results_per_page": 5,
            "sort_by": "date",
            "content-type": "application/json"
        }

        response = requests.get(url, params=params)
        state["job_results"] = response.json()

    except Exception as e:
        state["errors"] = str(e)

    return state


# 5. COMPANY INSIGHTS AGENT



def company_insights(state: PlannerState):
    jobs_data = state.get("job_results")
    jobs = jobs_data.get("results", [])

    insights = []

    for job in jobs:
        company = job.get("company", {}).get("display_name")


        # API Request
        url = "https://serpapi.com/search"

        params = {
            "engine": "google",
            "q": f"{company} company",
            "api_key": INSIGHTS
        }

        try:

            response = requests.get(
                url,
                params=params
            )

            data = response.json()

            kg = data.get("knowledge_graph", {})

            if not kg:
                continue

            company_data = {
                "Company Name": kg.get("title"),
                "Type": kg.get("type"),
                "Website": kg.get("website"),
                "Description": kg.get("description"),
                "Founded": kg.get("founded"),
                "Headquarters": kg.get("headquarters"),
                "CEO": kg.get("ceo"),
                "Revenue": kg.get("revenue"),
                "Employees": kg.get("employees"),
                "Stock Price": kg.get("stock_price"),
                "Subsidiaries": kg.get("subsidiaries")
            }

            insights.append(company_data)

        except Exception as e:
            state["errors"] = str(e)
            return state

    state["company_insights"] = insights
    return state


# 6. RESUME OPTIMIZATION AGENT


def resume_opt(state:PlannerState):
    resume=state["resume_text"]
    jobs=state["job_results"]

    prompt = f"""
    Analyze this resume according to given jobs.

    Tasks:
    1. Find missing skills
    2. Improve ATS keywords
    3. Rewrite weak bullet points
    4. Improve projects section
    5. Optimize for recruiters
    6. Return complete optimized resume

    Resume:
    {resume}
    
    Jobs:
    {jobs}
    
    """

    response = llm.invoke(prompt)

    return{
        **state,
        "optimized_resume_text":response.content
    }


# 7. ITINERARY AGENT


def itinerary_agent(state:PlannerState):

    if state.get("errors"):
        return state

    if not state.get("resume_file_path"):
        state["errors"] = "Please add your Resume."

    if not state.get("skills"):
        state["errors"] = "Add skills in your Portfolio."

    if not state.get("experience"):
        state["errors"] = "Add experience in your Resume."

    if not state.get("projects"):
        state["errors"] = "Add projects in your portfolio."




    try:

        name = "" if not state.get("name") else state.get("name")
        email = "" if not state.get("email") else state.get("email")
        role = "" if not state.get("inferred_role") else state.get("inferred_role")
        skills = [] if not state.get("skills") else state.get("skills")
        projects = [] if not state.get("projects") else state.get("projects")
        experience = "" if not state.get("experience") else state.get("experience")
        education = "" if not state.get("education") else state.get("education")
        jobs = [] if not state.get("job_results") else state.get("job_results")
        company_insights = [] if not state.get("company_insights") else state.get("company_insights")
        optimized_resume = "" if not state.get("optimized_resume_text") else state.get("optimized_resume_text")

        prompt = f"""
            You are a professional AI Career Coach and Resume Optimization Expert.

            Your task is to generate a complete AI-powered career report for the user.
            
            ========================
            USER DETAILS
            ========================
            
            Name:
            {name}
            
            Email:
            {email}
            
            Target Role:
            {role}
            
            Skills:
            {skills}
            
            Projects:
            {projects}
            
            Experience:
            {experience}
            
            Education:
            {education}
            
            Job Search Results:
            {jobs}
            
            Company Insights:
            {company_insights}
            
            Optimized Resume:
            {optimized_resume}
            
            ========================
            OUTPUT FORMAT
            ========================
            
            Generate the response in the exact order below with professional formatting, clear headings, bullet points, and motivating language.
            
            # 1. Resume Overview
            
            Show all extracted information from the user's resume in a structured format.
            
            Include:
            - Name
            - Email
            - Target Role
            - Skills
            - Projects
            - Experience
            - Education 
            
            Make this section clean and recruiter-friendly.
            
            --------------------------------------------------
            
            # 2. Available Jobs
            
            Show all job opportunities with there content from the "jobs" variable.
            
            Show each job seprate with serial number.
            
            
            
            Format jobs professionally using bullets or cards style.
            
            If no jobs are available in "jobs" variable, say:
            "No matching jobs found currently. Improve skills and retry search."
            
            --------------------------------------------------
            
            # 3. About Companies
            
            Show company insights from the "company_insights" variable.
            
            For EACH company include:
            - Company Name
            - Industry
            - Website
            - linkdin
            - employee-count
            - Headquarters
            - Description
            - Technologies
            - funding
            - remote_friendly
            - hiring_status
            
            Make this section informative and motivational.
            
            --------------------------------------------------
            
            # 4. Optimised Resume
            
            Show the content from "optimized_resume" variable

            """

        response = llm.invoke(prompt)
        state["itinerary"] = response.content

    except Exception as e:
        state["errors"] = str(e)
        state["itinerary"] = None

    return state

# 8. ERROR HANDLING AGENT


def error_handler(state:PlannerState):
    if state.get("errors"):
        print("Error ❌",state["errors"])
    else:
        print(state["itinerary"])

# ===================
# BUILD STATEGRAPH
# ===================


workflow = StateGraph(PlannerState)

workflow.add_node("textconverter", textconverter)
workflow.add_node("input_parser_agent", input_parser_agent)
workflow.add_node("role_inference_agent", role_inference_agent)
workflow.add_node("job_search", job_search)
workflow.add_node("company_insights", company_insights)
workflow.add_node("resume_opt", resume_opt)
workflow.add_node("itinerary_agent", itinerary_agent)
workflow.add_node("error_handler", error_handler)

workflow.set_entry_point("textconverter")

workflow.add_edge("textconverter", "input_parser_agent")
workflow.add_edge("input_parser_agent", "role_inference_agent")
workflow.add_edge("role_inference_agent", "job_search")
workflow.add_edge("job_search", "company_insights")
workflow.add_edge("company_insights", "resume_opt")
workflow.add_edge("resume_opt", "itinerary_agent")
workflow.add_edge("itinerary_agent", "error_handler")
workflow.add_edge("error_handler", END)

app = workflow.compile()

# ==============
# JOB AGENT
# ==============


def job_agent(user_input):
    initial_state: PlannerState = {
        "resume_file_path": user_input,
        "resume_text": None,
        "name": None,
        "email": None,
        "location" :None,
        "skills": None,
        "projects": None,
        "experience": None,
        "education": None,
        "resume_date": None,
        "inferred_role": None,
        "job_results": None,
        "company_insights": None,
        "optimized_resume_text": None,
        "itinerary": None,
        "errors": None
    }

    final_result = app.invoke(initial_state)

    return final_result

