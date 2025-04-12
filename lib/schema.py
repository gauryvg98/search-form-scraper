from pydantic import BaseModel, Field
from typing import Optional

class WebElement(BaseModel):
    id: Optional[str] = Field(default=None, description="ID of the element")
    xpath: str = Field(
        description="XPath selector to find element"
    )
    css_selector: Optional[str] = Field(
        default=None, description="CSS selector to find element"
    )
    index: Optional[int] = Field(
        default=None, description="Index if multiple elements match"
    )
    element_description: Optional[str] = Field(
        default=None, description="Description of the element being interacted with"
    )


class WebSearchSchema(BaseModel):
    detail_page_link: WebElement
    submit_button: WebElement
    next_page_button: WebElement
    search_page_url: str
