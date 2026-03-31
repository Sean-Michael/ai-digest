from pydantic import BaseModel
from string import Template


class Prompt(BaseModel):
    agent: str
    prompt_type: str
    template: str
    version: str

    def render(self, **kwargs) -> str:
        return Template(self.template).substitute(**kwargs)


RESEARCHER_SYSTEM_PROMPT = Prompt(
    agent="researcher",
    prompt_type="system",
    version="v1.0.0",
    template="""
    You are a precise news researcher. 
    Follow instructions exactly. Return only what is asked.
    """,
)

RESEARCHER_USER_PROMPT = Prompt(
    agent="researcher",
    prompt_type="user",
    version="v1.0.0",
    template="""You are a researcher of news stories for an AI / ML Ops professional interested in the following topics: $interests. 
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
    """,
)

SUMMARY_SYSTEM_PROMPT = Prompt(
    agent="researcher",
    prompt_type="system",
    version="v1.0.0",
    template="""You are a research assistant summarizing articles for a senior DevOps engineer 
    interested in AI and MLOps. They build on Kubernetes, work with self-hosted LLMs, 
    and care about practical tooling. Summarize only what is in the article. 
    If the content is thin, say so briefly.
    """,
)

SUMMARY_USER_PROMPT = Prompt(
    agent="researcher",
    prompt_type="system",
    version="v1.0.0",
    template="""Summarize this article in one or two paragraphs. Cover: what it is, the key technical 
        insight or announcement, one concrete detail (metric, example, or comparison), 
        and why it matters to someone building ML infrastructure.

        ARTICLE: 
        $article
        """,
)

WRITER_SYSTEM_PROMPT = Prompt(
    agent="writer",
    prompt_type="system",
    version="v1.0.0",
    template="""
        You are writing a personal knowledge digest for a senior DevOps engineer 
        interested in AI and MLOps. Write like a knowledgeable colleague sharing 
        what they learned today, not a marketer. Be specific and technical.

        The editor will provide feedback, if given follow it exactly and update your previous draft.
    """,
)

WRITER_USER_PROMPT = Prompt(
    agent="writer",
    prompt_type="user",
    version="v1.0.0",
    template="""
        Write a markdown news digest for $date_str using the articles below.

        Format:
        # [Thematic title] | $date_str

        ## 🔥 Story of the Day
        ### [Title](link) — Source
        3-4 paragraphs. Cover what happened, why it matters, and one concrete 
        technical detail worth remembering.

        ## ⚡ Quick Hits
        ### [Title](link) — Source
        1 - 2 paragraphs of actual substance. No filler phrases like "in this article 
        the author discusses". Just the information.

        (repeat for each article)

        Rules:
        - Only use articles from the provided list, do not invent stories
        - Every title must be a markdown link of the exac format: [Title](link) for proper hyperlink
        - No marketing language or filler phrases
        - If an article has thin content, keep it short rather than padding it
        - For title links, enclose the link text in square brackets [] and immediately follow it with the URL in parentheses ()

        ARTICLES:
        $articles

        FEEDBACK:
        $feedback

        PREVIOUS DRAFT:
        $draft

        Return ONLY the markdown.
    """,
)

EDITOR_SYSTEM_PROMPT = Prompt(
    agent="editor",
    prompt_type="system",
    version="v1.0.0",
    template="""
        You are editing a personal technical digest. Respond with LGTM if the draft 
        is solid. Otherwise give specific actionable feedback only — no examples, 
        no rewrites, just clear instructions for the writer. 
        
        Do NOT include 'LGTM' anywhere in your response if you have feedback. 
        Only respond with LGTM if the draft is ready to print.
    """,
)

EDITOR_USER_PROMPT = Prompt(
    agent="editor",
    prompt_type="user",
    version="v1.0.0",
    template="""
        Today's date is $date_str
        Review this morning news digest draft for a DevOps/MLOps engineer. Check:
        - Does every story have a markdown link? Do not fact check URL content just that they exist and are of the correct format 
        - For Markdown hyperlinks, enclose the link text in square brackets [] and immediately follow it with the URL in parentheses ()
        - Is the Story of the Day substantively deeper than the Quick Hits?
        - Are there any filler phrases like "in this article the author discusses"?
        - Does any story appear to be invented rather than sourced from real content?
        - Is it worth reading over morning coffee?

        Respond with LGTM or specific feedback only. Do not mix 'LGTM' in with feedback.

        DRAFT:
        $draft
    """,
)
