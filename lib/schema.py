from typing import List, Optional

from pydantic import BaseModel, Field


class WebElement(BaseModel):
    id: Optional[str] = Field(default=None, description="ID of the element")
    xpath: str = Field(description="XPath selector to find element")
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
    do_perform_search: Optional[bool] = Field(
        default=True, description="Whether to perform a search"
    )
    detail_page_link: WebElement
    submit_button: WebElement
    next_page_button: WebElement
    search_page_url: str
    pre_search_steps: Optional[List[WebElement]] = Field(
        default=[], description="Clicks before searching"
    )
    post_search_steps: Optional[List[WebElement]] = Field(
        default=[], description="Clicks after searching"
    )


class PropertyData(BaseModel):
    address: Optional[str] = Field(None, description="Property address")
    city: Optional[str] = Field(None, description="City where property is located")
    state: Optional[str] = Field(None, description="State where property is located")
    zip: Optional[str] = Field(None, description="ZIP/Postal code")
    price: Optional[float] = Field(None, description="Property price in USD")
    sqft: Optional[float] = Field(None, description="Property area in square feet")
    beds: Optional[int] = Field(None, description="Number of bedrooms")
    baths: Optional[float] = Field(None, description="Number of bathrooms")
    property_image_urls: List[str] = Field(
        default_factory=list, description="List of property image URLs"
    )
    brochure_doc_urls: List[str] = Field(
        default_factory=list, description="List of PDF brochure URLs"
    )
    property_type: Optional[str] = Field(
        None, description="Type of property (e.g., residential, commercial)"
    )
    property_description: Optional[str] = Field(
        None, description="Detailed property description"
    )
    broker: Optional[str] = Field(None, description="Name of the broker/agent")
    broker_url: Optional[str] = Field(None, description="URL of the broker's website")
    broker_phone: Optional[str] = Field(None, description="Broker's phone number")
    broker_email: Optional[str] = Field(None, description="Broker's email address")
    broker_address: Optional[str] = Field(None, description="Broker's office address")
    source_url: Optional[str] = Field(None, description="URL of the source page")
