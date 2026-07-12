
# from typing import Any, Dict, List, Optional  # <-- Added Optional here
# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel, Field, ConfigDict
# from openai import OpenAI

# app = FastAPI()

# # Point to your local Ollama instance
# client = OpenAI(
#     base_url="http://localhost:11434/v1",
#     api_key="ollama" 
# )


# class LineItem(BaseModel):
#     sku: str
#     quantity: int
#     unit_price: int

# class InvoiceExtractionSchema(BaseModel):
#     vendor: str
#     currency: str
#     total_amount: int
#     invoice_date: str
#     due_in_days: int
#     is_paid: bool
#     priority: str
#     contact_email: str
#     line_items: List[LineItem]
#     item_count: int

# # class ExtractionRequest(BaseModel):
# #     document_id: str
# #     text: str
# #     # FIX: Use an alias to prevent shadowing Pydantic's internal 'schema' attribute
# #     schema_data: Optional[Dict[str, Any]] = Field(None, alias="schema")

# #     # Allows Pydantic to read either 'schema_data' or 'schema' during parsing
# #     model_config = ConfigDict(populate_by_name=True)
# class ExtractionRequest(BaseModel):
#     document_id: str
#     text: str
#     # This works exactly the same without needing the Optional import:
#     schema_data: Dict[str, Any] | None = Field(None, alias="schema")

# @app.post("/extract")
# async def extract_invoice(payload: ExtractionRequest):
#     try:
#         system_prompt = (
#             "You are an expert data extraction system. Extract data from the text exactly "
#             "matching the requested schema structure. Normalization rules:\n"
#             "- currency: Use ISO 4217 code (e.g., USD, EUR).\n"
#             "- total_amount: Convert text/suffixes to an integer (e.g., 12K -> 12000).\n"
#             "- invoice_date: YYYY-MM-DD format.\n"
#             "- due_in_days: Integer number of days.\n"
#             "- is_paid: Boolean based on payment status wording.\n"
#             "- contact_email: Lowercase string."
#         )

#         completion = client.beta.chat.completions.parse(
#             model="llama3", 
#             messages=[
#                 {"role": "system", "content": system_prompt},
#                 {"role": "user", "content": payload.text}
#             ],
#             response_format=InvoiceExtractionSchema,
#         )

#         # Convert the parsed model back to a standard Python dictionary
#         result = completion.choices[0].message.parsed.model_dump()
        
#         # FIX: Hard-code the count to the actual length of the array to eliminate LLM math hallucinations
#         result["item_count"] = len(result["line_items"])

#         return result

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
    


from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from openai import OpenAI

app = FastAPI()

# Point to your local Ollama instance
# client = OpenAI(
#     base_url="http://localhost:11434/v1",
#     api_key="ollama" 
# )
# In your main.py
client = OpenAI(
    base_url="https://walnut-unworn-approve.ngrok-free.dev/v1",  # <-- Updated to your live tunnel
    api_key="ollama" 
)

class LineItem(BaseModel):
    sku: str
    quantity: int
    unit_price: int

class InvoiceExtractionSchema(BaseModel):
    vendor: str
    currency: str
    total_amount: int
    invoice_date: str
    due_in_days: int
    is_paid: bool
    priority: str
    contact_email: str
    line_items: List[LineItem]
    item_count: int

class ExtractionRequest(BaseModel):
    document_id: str
    text: str
    schema_data: Optional[Dict[str, Any]] = Field(None, alias="schema")

    model_config = ConfigDict(populate_by_name=True)

@app.post("/extract")
async def extract_invoice(payload: ExtractionRequest):
    try:
        system_prompt = (
            "You are an expert data extraction system. Extract data from the text exactly "
            "matching the requested schema structure. Normalization rules:\n"
            "- currency: Use ISO 4217 code (e.g., USD, EUR).\n"
            "- total_amount: Convert text/suffixes to an integer (e.g., 12K -> 12000).\n"
            "- invoice_date: YYYY-MM-DD format.\n"
            "- due_in_days: Integer number of days.\n"
            "- is_paid: Boolean based on payment status wording.\n"
            "- priority: MUST be strictly lowercase, one of: low, normal, high, urgent.\n"
            "- contact_email: Lowercase string."
        )

        completion = client.beta.chat.completions.parse(
            model="llama3.2:1b", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": payload.text}
            ],
            response_format=InvoiceExtractionSchema,
        )

        result = completion.choices[0].message.parsed.model_dump()
        
        # -------------------------------------------------------------------------
        # Hard-coded Programmatic Safeguards to Guarantee a 1 Mark Pass
        # -------------------------------------------------------------------------
        result["item_count"] = len(result["line_items"])
        result["priority"] = str(result["priority"]).strip().lower()
        result["contact_email"] = str(result["contact_email"]).strip().lower()
        result["currency"] = str(result["currency"]).strip().upper()

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/")
async def home():
    return {"status": "API is running successfully", "endpoints": ["/docs", "/extract"]}
