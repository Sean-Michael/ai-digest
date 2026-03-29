from pydantic import BaseModel
from string import Template

class Prompt(BaseModel):
    agent: str
    prompt_type: str
    prompt: str

    def render(self, **kwargs) -> str:
        return Template(self.prompt).substitute(**kwargs)


RESEARCHER_SYSTEM_PROMPT = Prompt(
    agent="researcher",
    prompt_type="system",
    prompt="""
    You are a precise news researcher. 
    Follow instructions exactly. Return only what is asked.
    """)

RESEARCHER_USER_PROMPT = Prompt(
    agent="researcher",
    prompt_type="user",
    prompt="""You are a researcher of news stories for an AI / ML Ops professional interested in the following topics: $interests. 
    Specifically focus on new technology or product releases, workflows, techniques, or otherwise 'technical' content rather than social or political.
    Given a list of articles in the following format:
            "source": source,
            "title": entry.title,
            "summary": entry.summary,
            "link": entry.link
    
    1. Select no more than 10 articles that best match the interest topics and criteria.
        - Try to use a mixture of sources to capture a variety of topics.
        - Prioritize content from: Hugging Face Blog, MLOps Community, CNCF Blog when available
    2. Gather the UNIQUE links for each article 
    3. Return ONLY a JSON array of selected article links, nothing else. Example format:
["https://...", "https://..."]
    
    ARTICLES:
    $articles
    """)