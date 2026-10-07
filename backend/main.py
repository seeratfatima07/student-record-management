from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client
from dotenv import load_dotenv
from google import genai
import os
import json


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Supabase URL or key is missing from .env")

if not GEMINI_API_KEY:
    raise RuntimeError("Gemini API key is missing from .env")


# =========================================================
# CONNECTIONS
# =========================================================

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

gemini_client = genai.Client(
    api_key=GEMINI_API_KEY
)


# =========================================================
# FASTAPI APP
# =========================================================

app = FastAPI(
    title="Student Record Management API",
    description="CRUD API with Supabase and Gemini AI",
    version="2.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# MODELS
# =========================================================

class Record(BaseModel):
    full_name: str
    phone_number: str


class RecordUpdate(BaseModel):
    full_name: str
    phone_number: str


class AIPrompt(BaseModel):
    prompt: str


# =========================================================
# HOME
# =========================================================

@app.get("/")
def home():

    return {
        "message":
        "Student Record Management API is running"
    }


# =========================================================
# NORMAL CRUD
# =========================================================


# READ
@app.get("/records")
def get_records():

    try:

        response = (
            supabase
            .table("records")
            .select("*")
            .execute()
        )

        return response.data

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# CREATE
@app.post("/records")
def create_record(record: Record):

    try:

        response = (
            supabase
            .table("records")
            .insert({
                "full_name":
                    record.full_name,

                "phone_number":
                    record.phone_number
            })
            .execute()
        )

        return response.data

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# UPDATE
@app.put("/records/{record_id}")
def update_record(
    record_id: int,
    record: RecordUpdate
):

    try:

        response = (
            supabase
            .table("records")
            .update({
                "full_name":
                    record.full_name,

                "phone_number":
                    record.phone_number
            })
            .eq("id", record_id)
            .execute()
        )

        return response.data

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# DELETE
@app.delete("/records/{record_id}")
def delete_record(record_id: int):

    try:

        response = (
            supabase
            .table("records")
            .delete()
            .eq("id", record_id)
            .execute()
        )

        return response.data

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =========================================================
# AI CRUD
# =========================================================

@app.post("/ai-command")
def ai_command(request: AIPrompt):

    try:

        # -------------------------------------------------
        # Ask Gemini to understand the command
        # -------------------------------------------------

        instruction = f"""
You are an AI assistant for a Student Record Management
System.

Determine which CRUD operation the user wants.

Allowed operations:

CREATE
READ
UPDATE
DELETE

Return ONLY valid JSON.
Do not use markdown.
Do not explain anything.

Use this exact structure:

{{
    "operation": "CREATE or READ or UPDATE or DELETE",
    "full_name": null,
    "phone_number": null,
    "new_full_name": null,
    "new_phone_number": null
}}

Rules:

CREATE:
full_name and phone_number contain the new student's data.

READ:
If the user asks for all records, full_name should be null.
If the user asks for a particular student, put that student's
name in full_name.

UPDATE:
full_name is the CURRENT name of the student.
new_full_name is the new name only if the user wants to
change the name.
new_phone_number is the new phone number only if the user
wants to change the phone number.

DELETE:
full_name is the name of the student to delete.

Use null for information that is not required.

User request:
{request.prompt}
"""


        response = (
            gemini_client
            .models
            .generate_content(
                model="gemini-3.8-flash",
                contents=instruction
            )
        )


        if not response.text:

            raise HTTPException(
                status_code=400,
                detail="Gemini returned no response."
            )


        ai_text = (
            response.text
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )


        command = json.loads(ai_text)


        operation = str(
            command.get(
                "operation",
                ""
            )
        ).upper()


        full_name = command.get(
            "full_name"
        )

        phone_number = command.get(
            "phone_number"
        )

        new_full_name = command.get(
            "new_full_name"
        )

        new_phone_number = command.get(
            "new_phone_number"
        )


        # =================================================
        # AI CREATE
        # =================================================

        if operation == "CREATE":

            if (
                not full_name
                or not phone_number
            ):

                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Please provide both the "
                        "student name and phone number."
                    )
                )


            db_response = (
                supabase
                .table("records")
                .insert({
                    "full_name":
                        str(full_name).strip(),

                    "phone_number":
                        str(phone_number).strip()
                })
                .execute()
            )


            return {
                "operation": "CREATE",

                "message":
                    f"{full_name} was added successfully.",

                "records":
                    db_response.data
            }


        # =================================================
        # AI READ
        # =================================================

        elif operation == "READ":

            # Read particular student
            if full_name:

                db_response = (
                    supabase
                    .table("records")
                    .select("*")
                    .ilike(
                        "full_name",
                        f"%{full_name}%"
                    )
                    .execute()
                )

            # Read all students
            else:

                db_response = (
                    supabase
                    .table("records")
                    .select("*")
                    .execute()
                )


            return {
                "operation": "READ",

                "message":
                    f"Found {len(db_response.data)} record(s).",

                "records":
                    db_response.data
            }


        # =================================================
        # AI UPDATE
        # =================================================

        elif operation == "UPDATE":

            if not full_name:

                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Please specify which "
                        "student to update."
                    )
                )


            # Find student first
            existing = (
                supabase
                .table("records")
                .select("*")
                .ilike(
                    "full_name",
                    f"%{full_name}%"
                )
                .execute()
            )


            if not existing.data:

                raise HTTPException(
                    status_code=404,
                    detail=(
                        f"No student named "
                        f"{full_name} was found."
                    )
                )


            # Prevent accidentally modifying multiple
            # students with the same/similar name.
            if len(existing.data) > 1:

                raise HTTPException(
                    status_code=400,
                    detail=(
                        "More than one matching student "
                        "was found. Please use a more "
                        "specific name."
                    )
                )


            student = existing.data[0]

            record_id = student["id"]


            updated_name = (
                new_full_name
                if new_full_name
                else student["full_name"]
            )


            updated_phone = (
                new_phone_number
                if new_phone_number
                else student["phone_number"]
            )


            if (
                not new_full_name
                and not new_phone_number
            ):

                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Please specify what information "
                        "should be updated."
                    )
                )


            db_response = (
                supabase
                .table("records")
                .update({
                    "full_name":
                        str(updated_name).strip(),

                    "phone_number":
                        str(updated_phone).strip()
                })
                .eq(
                    "id",
                    record_id
                )
                .execute()
            )


            return {
                "operation": "UPDATE",

                "message":
                    f"{full_name} was updated successfully.",

                "records":
                    db_response.data
            }


        # =================================================
        # AI DELETE
        # =================================================

        elif operation == "DELETE":

            if not full_name:

                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Please specify which "
                        "student to delete."
                    )
                )


            # Find student first
            existing = (
                supabase
                .table("records")
                .select("*")
                .ilike(
                    "full_name",
                    f"%{full_name}%"
                )
                .execute()
            )


            if not existing.data:

                raise HTTPException(
                    status_code=404,
                    detail=(
                        f"No student named "
                        f"{full_name} was found."
                    )
                )


            # Safety: do not delete multiple similar names
            if len(existing.data) > 1:

                raise HTTPException(
                    status_code=400,
                    detail=(
                        "More than one matching student "
                        "was found. Please use a more "
                        "specific name."
                    )
                )


            student = existing.data[0]

            record_id = student["id"]


            db_response = (
                supabase
                .table("records")
                .delete()
                .eq(
                    "id",
                    record_id
                )
                .execute()
            )


            return {
                "operation": "DELETE",

                "message":
                    f"{student['full_name']} was deleted successfully.",

                "records":
                    db_response.data
            }


        # =================================================
        # UNKNOWN COMMAND
        # =================================================

        else:

            raise HTTPException(
                status_code=400,
                detail=(
                    "AI could not determine the "
                    "CRUD operation."
                )
            )


    except HTTPException:

        raise


    except json.JSONDecodeError:

        raise HTTPException(
            status_code=500,
            detail=(
                "Gemini returned an invalid "
                "response format."
            )
        )


    except Exception as e:

        print(
            "AI COMMAND ERROR:",
            repr(e)
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )