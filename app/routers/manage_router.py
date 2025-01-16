import random
import bcrypt
from fastapi import APIRouter, BackgroundTasks
from faker import Faker

from app.db import get_conn

fake = Faker()
router = APIRouter(prefix="/manage")

# @router.get("/ping")
# def ping():
#     with get_conn() as conn:
#         cursor = conn.cursor()
#         cursor.execute("select 1")
#         record = cursor.fetchone()
#         cursor.close()
#         print(record)
#         return "pong"

def load_fake_data_task():
    print("executing load fake data")
    password = b"blogapi123"
    hashed = bcrypt.hashpw(password,bcrypt.gensalt())
    with get_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "insert into users (email,password,is_admin) values (%s, %s, %s)", 
                ["admin@example.com", hashed, True])

            for i in range(10):
                cursor.execute(
                    "insert into users (email, password) values (%s, %s)", 
                    [fake.email(), hashed]
                )
            
            for category in ["react", "fastapi", "springboot", "nextjs"]:
                cursor.execute("insert into categories (name) values (%s)", [category])
                
            for i in range(20):
                post = {
                    "user_id": 1,
                    "categorie_id": random.choice([1,2,3]),
                    "title": fake.sentence(nb_words=8),
                    "content": fake.paragraph(nb_sentences=5),
                    "status": random.choice(["draft","public","private"])
                }
                cursor.execute(
                    "insert into posts (user_id, categorie_id, title, content, status) values (%(user_id)s, %(categorie_id)s, %(title)s, %(content)s, %(status)s)",
                    post
                    )
            
@router.get("/ping")
def ping():
    with get_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            record = cursor.fetchone()
            print(record)
            return "pong"
        
@router.get("/load-fake-data")
def load_fake_data(background_tasks: BackgroundTasks):
    background_tasks.add_task(load_fake_data_task)
    return {"message": "load fake data running background"}