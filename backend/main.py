from fastapi import FastAPI, HTTPException

import motor.motor_asyncio
import os
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file
client = motor.motor_asyncio.AsyncIOMotorClient('mongodb+srv://zeynepkrtls01:ZRAZ2x5rw9AXMllc@sugradcluster.aro7tnh.mongodb.net/')
database = client.get_database("SuGrad")

from fastapi.middleware.cors import CORSMiddleware
from models.model import Course
from models.model import ScienceCourse
from fastapi.responses import JSONResponse  # Correct import for JSONResponse
from models.model import CourseRecommendation, UserRegistration, UserLogin, ChangePassword, UserInDB, UserAddInfo, AddPrevRecoom, UserGetAllResponse, SpecificRecom, CourseAdd, DeleteUser, ForgotPassword, VerifyCodeRequest, ResetPasswordRequest
from typing import List  # Import List from the typing module
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi.security import HTTPBearer
from config.database import database
from fastapi import Depends, HTTPException, status
from fastapi_mail import FastMail, MessageSchema, MessageType, ConnectionConfig

from datetime import datetime, timedelta
from fastapi import Body
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config.database import user_collection
from typing import Annotated
import json
from starlette.background import BackgroundTasks
from fastapi_mail import FastMail, MessageSchema, MessageType
from fastapi.security import HTTPAuthorizationCredentials
app = FastAPI()

oauth2_scheme = HTTPBearer()

from routers.router import(

    fetch_recommend_courses,
    add_prev_recoms,
    register_user,
    authenticate_user,
    create_access_token,
    get_current_user,
    update_password,
    add_user_info,
    get_all_user,
    delete_user,
    fetch_recommend_specific_courses,
    process_recommendation,
    process_content_recommendation,
    fetch_top_courses,
    fetch_least_courses,
    add_course_info_user,
    send_verification_email,
    generate_verification_code,
    get_user_info_by_email,
    update_user_password,
    fetch_user_stats
    
)
user_collection = database.get_collection("user")
#to allow frontend to access the backend
origins = ['https://localhost:3000']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
) 



#an example of a route
# @app.get("/")
# def read_root():
#      return {"Hello": "World"}
# @app.get("/items/")
# async def read_items(token: Annotated[str, Depends(oauth2_scheme)]):
#     return {"token": token}

@app.post("/user/login", tags=["User"])
async def login_for_access_token(user_data: UserLogin):
    user = await authenticate_user(user_data.username, user_data.password, user_collection)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, 
            "pdf_uploaded": user.pdf_uploaded,
            "success": True}



@app.post("/user/register", tags=["User"])
async def register_user_endpoint(user_data: UserRegistration):
    response = await register_user(user_data)
    if response:
        return response
    else:
        raise HTTPException(404, "Cannot register user")
    

@app.post("/user/changePassword", tags=["User"])
async def change_password(user_data: ChangePassword, current_user: UserInDB = Depends(get_current_user)):
    if not user_data.new_password == user_data.confirm_password:
        raise HTTPException(400, "Passwords do not match")
    else:
        response = await update_password(user_data, current_user)
        if response:
            return response
        else:
            raise HTTPException(404, "Cannot change password")
    
        # Update user's password
        new_hashed_password = get_password_hash(change_data.new_password)
        await update_password(user.username, new_hashed_password, user_collection)
        return {"message": "Password updated successfully"}
    
reset_tokens = {}

@app.post("/user/sendVerification", tags=["User"])
async def forget_password(
    background_tasks: BackgroundTasks,
    fpr: ForgotPassword,
):
    try:
        user = await get_user_info_by_email(user_collection, fpr)
        print("user", user.email )
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid Email address")
        
        verification_code = generate_verification_code(fpr.email)
        
        # Save the verification code and its expiration in the database or in-memory store (for simplicity, using a dict here)
        reset_tokens[fpr.email] = {
            "code": verification_code,
            "expires": datetime.utcnow() + timedelta(minutes=10)
        }

        # Send the email with the verification code
        background_tasks.add_task(send_verification_email, fpr.email, verification_code)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Verification code has been sent to your email", "success": True}
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e.detail)



# In-memory store for reset tokens (use a database in production)



@app.post("/user/verifyCode", tags=["User"])
async def verify_code(request: VerifyCodeRequest):
    verification_code = request.verification_code

    # Search for the email associated with the verification code
    email = None
    print("email", reset_tokens.items())
    for key, value in reset_tokens.items():
        if value["code"] == verification_code and value["expires"] > datetime.utcnow():
            email = key
            value["verified"] = True
            break

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code"
        )
    reset_tokens[email]['verified'] = True

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Verification code is valid", "success": True}
    )
    
@app.post("/user/resetPassword", tags=["User"])
async def reset_password(request: ResetPasswordRequest):
    #verification_code = request.verification_code
    new_password = request.new_password
    new_password_repeat = request.new_password_repeat

    if new_password != new_password_repeat:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )
    print("reset_tokens:", reset_tokens)  # Debugging statement
    # Search for the email associated with the verification code
    # Find the email that has been verified
    email = None
    for key, value in reset_tokens.items():
        if value.get('verified'):
            email = key
            break

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code has not been validated"
        )

    new_password = request.new_password

    # Update the user's password
    try:
        await update_user_password(user_collection, email, new_password)
        # Optionally, remove the verification code after successful password reset
        del reset_tokens[email]
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Password has been reset successfully", "success": True}
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    


@app.post("/user/stats", tags=["User"])
async def get_user_stats( token: HTTPAuthorizationCredentials = Depends(oauth2_scheme)):
    response = await fetch_user_stats(token)
    if response:
        return response
    else:
        raise HTTPException(404, "Cannot get user stats")
    

@app.post("/user/addInfo", tags=["User"])
async def add_user_info_route(user_info: UserAddInfo, token: HTTPAuthorizationCredentials = Depends(oauth2_scheme)):
    response = await add_user_info(user_info, token)
    if response:
        return response
    else:
        raise HTTPException(404, "Cannot add user info")


@app.post("/recommend/course", tags=["Recommend"])
async def get_course_recommendation(token: Annotated[str, Depends(oauth2_scheme)]):
    response = await fetch_recommend_courses(token)
    if response:
        return response
    else:
        raise HTTPException(404, "No courses found")


# @app.post("/course/addRecommended", tags=["Course"]) 
# async def add_course(courses: AddPrevRecoom, token: Annotated[str, Depends(oauth2_scheme)]):
#     response = await add_prev_recoms(courses, token)
#     if response:
#         return response
#     else:
#         raise HTTPException(404, "Cannot add course")

@app.post("/user/getAll", response_model=UserGetAllResponse, tags=["User"])
async def get_all_user_handler(token: HTTPAuthorizationCredentials = Depends(oauth2_scheme)):
    response = await get_all_user(token)
    if response:
        return response
    else:
        raise HTTPException(404, "No users found")

@app.delete("/user/delete", tags=["User"])
async def delete_user_handler(userData : DeleteUser, token: HTTPAuthorizationCredentials = Depends(oauth2_scheme)):
    response = await delete_user(userData, token)
    if response:
        return response
    else:
        raise HTTPException(404, "Cannot delete user")
    

@app.post("/recommend/specificCourse", tags=["Recommend"])
async def get_specific_course_recommendation(request: SpecificRecom, token: HTTPAuthorizationCredentials = Depends(oauth2_scheme)):
    response = await fetch_recommend_specific_courses(request, token)
    if response:
        return response
    else:
        raise HTTPException(404, "No courses found")


@app.post("/recommend/collabrativeFiltering", tags=["Recommend"])
async def recommend_courses(token: HTTPAuthorizationCredentials = Depends(oauth2_scheme)):
    return await process_recommendation(token)


@app.post("/recommend/contentBased", tags=["Recommend"])
async def recommend_courses(token: HTTPAuthorizationCredentials = Depends(oauth2_scheme)):
    return await process_content_recommendation(token)


@app.get("/course/getTop", tags=["Course"])
async def get_top_courses(token: HTTPAuthorizationCredentials = Depends(oauth2_scheme)):
    response =  await fetch_top_courses(token)
    if response:
        return response
    else:
        raise HTTPException(404, "No courses found")
    

@app.get("/course/getLeast", tags=["Course"])
async def get_top_courses(token: HTTPAuthorizationCredentials = Depends(oauth2_scheme)):
    response =  await fetch_least_courses(token)
    if response:
        return response
    else:
        raise HTTPException(404, "No courses found")
    

@app.post("/user/addCourse", tags=["User"], summary="Add course to user entity")
async def add_course(course: CourseAdd, token: HTTPAuthorizationCredentials = Depends(oauth2_scheme)):
    response = await add_course_info_user(course, token)
    if response:
        return response
    else:
        raise HTTPException(404, "Cannot add course")