import streamlit as st
from st_supabase_connection import SupabaseConnection

# Initialize Supabase client
# supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


def create_supabase_connection():
    sb_connection = st.connection(name="ST_SUPAB", type=SupabaseConnection, ttl=None)
#     # url="YOUR_SUPABASE_URL", # not needed if provided as a streamlit secret
#     # key="YOUR_SUPABASE_KEY", # not needed if provided as a streamlit secret
    return sb_connection




# Function to perform Supabase sign-up
def supabase_sign_up(sb_connection, email, password):
    # Perform sign-up using the Supabase client
    res = sb_connection.auth.sign_up(
        dict(email=email, password=password, options=dict(data=dict(fname="", attribution="")))
    )

    st.write(res)
    error = 0
    user = "user"
    if error:
        st.error(f"Sign up failed: {error.message}")
    else:
        st.success("Sign up successful!")
        return user


# Function to perform Supabase sign-in
def supabase_sign_in(sb_connection, email, password):
    # Perform sign-in using the Supabase client
    res = sb_connection.auth.sign_in_with_password(dict(email=email, password=password))

    st.write(res)
    error = 0
    user = "user"

    if error:
        st.error(f"Sign in failed: {error.message}")
    else:
        st.success("Sign in successful!")
        return user


# Streamlit UI for sign-up
sb_connection = create_supabase_connection()

signin, signup = st.tabs(["Sign-in", "Sign-up"])

with signin:
    username1 = st.text_input("Username")
    password1 = st.text_input("Password", type="password")
    if st.button("Sign In"):
        user = supabase_sign_in(sb_connection, username1, password1)

with signup:
    username = st.text_input("Username", key=10)
    password = st.text_input("Password", type="password", key=11)
    if st.button("Sign Up"):
        user = supabase_sign_up(sb_connection, username, password)
