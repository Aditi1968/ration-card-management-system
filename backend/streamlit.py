import streamlit as st
import mysql.connector
from mysql.connector import Error
import hashlib
from functools import wraps
from mysql.connector import Error
import pandas as pd

# MySQL connection function
def create_connection():
    try:
        connection = mysql.connector.connect(
            host='127.0.0.1',
            port='3306',  
            user='root',
            password='$$$$',
            database='rcms1'
        )
        if connection.is_connected():
            return connection
    except Error as e:
        st.error(f"Error connecting to MySQL: {e}")
        return None


# MySQL query execution
def execute_query(query, params=None):
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            connection.commit()
            return cursor
        except Error as e:
            st.error(f"Error executing query: {e}")
        finally:
            cursor.close()
            connection.close()

# Function to fetch data
def fetch_data(query, params=None):
    connection = create_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
        except Error as e:
            st.error(f"Error fetching data: {e}")
        finally:
            cursor.close()
            connection.close()

# Initialize session state for authentication
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'username' not in st.session_state:
    st.session_state.username = None

def register_user(username, password, role):
    # Add debug output
    st.write(f"Attempting to register user: {username} with role: {role}")
    
    query = "INSERT INTO USERS (username, password, role) VALUES (%s, %s, %s)"
    execute_query(query, (username, password, role))
    st.success("User registered successfully!")



    

def authenticate_user(username, password):
    connection = create_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        try:
            # Add debug output
            st.write(f"Attempting to authenticate user: {username}")
            
            # Print the actual query and parameters being used
            query = "SELECT * FROM USERS WHERE username = %s AND password = %s"
            st.write("Query:", query)
            st.write("Parameters:", (username, password))
            
            cursor.execute(query, (username, password))
            user = cursor.fetchone()
            if user:
                return user['username'], user['role']
            return None, None
        except Error as e:
            st.error(f"Authentication error: {e}")
            return None, None
        finally:
            cursor.close()
            connection.close()
    else:
        # Always return a tuple, even if connection fails
        return None, None

def login_form():
    st.subheader("Login")
    
    # Add a debug section
    st.write("Debug Information:")
    st.write("Current session state:", st.session_state)
    
    input_username = st.text_input("Username")
    input_password = st.text_input("Password", type="password")

    if st.button("Login"):
        # Add debug output
        st.write("Login button clicked")
        st.write(f"Attempting login with username: {input_username}")
        
        auth_username, role = authenticate_user(input_username, input_password)
        if auth_username and role:
            st.session_state.authenticated = True
            st.session_state.user_role = role
            st.session_state.username = auth_username
            st.success(f"Welcome, {auth_username}!")
            st.rerun()
        else:
            # Add more detailed error message
            st.error("Invalid username or password. Please check your credentials and try again.")
            # Add debug output for database connection
            connection = create_connection()
            if not connection:
                st.error("Failed to connect to database. Please check database connection.")

def logout():
    st.session_state.authenticated = False
    st.session_state.user_role = None
    st.session_state.username = None
    st.rerun()  # Updated from experimental_rerun
    
    # Trigger rerun by setting query parameters (without any actual params)
    st.experimental_set_query_params()

# Role-based access decorator

def role_required(allowed_roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not st.session_state.authenticated:
                st.error("You need to be logged in to access this feature.")
                return None
            
            if st.session_state.user_role not in allowed_roles:
                st.error(f"Access denied. Required roles: {', '.join(allowed_roles)}")
                return None
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Add the role decorators to your existing operations
@role_required(['Admin'])
def admin_operations(operation):
    if operation == "Add":
        st.subheader("Add New Admin")
        admin_id = st.text_input("Admin ID")
        a_fname = st.text_input("First Name")
        a_lname = st.text_input("Last Name")
        a_email = st.text_input("Email")
        dob = st.date_input("Date of Birth")
        age = st.number_input("Age", min_value=18)
        street_no = st.text_input("Street No.")
        pin = st.text_input("PIN")
        if st.button("Submit Admin"):
            query = "INSERT INTO ADMIN (Admin_id, A_Fname, A_Lname, A_Email_id, DOB, Age, Street_no, PIN) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
            params = (admin_id, a_fname, a_lname, a_email, dob, age, street_no, pin)
            execute_query(query, params)
            st.success(f"Admin {a_fname} {a_lname} added successfully!")

    elif operation == "View":
        admins = fetch_data("SELECT * FROM ADMIN")
        if admins:
            df = pd.DataFrame(admins)
            column_names = {
                'Admin_id': 'Admin ID',
                'A_Fname': 'First Name',
                'A_Lname': 'Last Name',
                'A_Email_id': 'Email',
                'DOB': 'Date of Birth',
                'Age': 'Age',
                'Street_no': 'Street No',
                'PIN': 'PIN'
            }
            df = df.rename(columns=column_names)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No admin records found.")

    elif operation == "Edit":
        st.subheader("Edit Admin")
        admins = fetch_data("SELECT Admin_id, A_Fname, A_Lname FROM ADMIN")
        admin_options = {f"{admin['A_Fname']} {admin['A_Lname']}": admin['Admin_id'] for admin in admins}
        selected_admin = st.selectbox("Select Admin to Edit", options=admin_options.keys())
        if selected_admin:
            admin_id = admin_options[selected_admin]
            admin_data = fetch_data("SELECT * FROM ADMIN WHERE Admin_id = %s", (admin_id,))[0]
            a_fname = st.text_input("First Name", admin_data["A_Fname"])
            a_lname = st.text_input("Last Name", admin_data["A_Lname"])
            a_email = st.text_input("Email", admin_data["A_Email_id"])
            dob = st.date_input("Date of Birth", admin_data["DOB"])
            age = st.number_input("Age", value=admin_data["Age"], min_value=18)
            street_no = st.text_input("Street No.", admin_data["Street_no"])
            pin = st.text_input("PIN", admin_data["PIN"])
            if st.button("Update Admin"):
                query = "UPDATE ADMIN SET A_Fname = %s, A_Lname = %s, A_Email_id = %s, DOB = %s, Age = %s, Street_no = %s, PIN = %s WHERE Admin_id = %s"
                params = (a_fname, a_lname, a_email, dob, age, street_no, pin, admin_id)
                execute_query(query, params)
                st.success(f"Admin {a_fname} {a_lname} updated successfully!")

    elif operation == "Remove":
        st.subheader("Remove Admin")
        admins = fetch_data("SELECT Admin_id, A_Fname, A_Lname FROM ADMIN")
        admin_options = {f"{admin['A_Fname']} {admin['A_Lname']}": admin['Admin_id'] for admin in admins}
        selected_admin = st.selectbox("Select Admin to Remove", options=admin_options.keys())
        if selected_admin:
            admin_id = admin_options[selected_admin]
            if st.button(f"Confirm Remove {selected_admin}"):
                query = "DELETE FROM ADMIN WHERE Admin_id = %s"
                execute_query(query, (admin_id,))
                st.success(f"Admin {selected_admin} removed successfully!")


@role_required(['Admin', 'Shopkeeper'])
def shopkeeper_operations(operation):
    if operation == "Add":
        st.subheader("Add New Shopkeeper")
        shopkeeper_id = st.text_input("Shopkeeper ID")
        s_fname = st.text_input("First Name")
        s_lname = st.text_input("Last Name")
        store_name = st.text_input("Store Name")
        street_no = st.text_input("Street No.")
        city = st.text_input("City")
        pin = st.text_input("PIN")
        admin_id = st.text_input("Admin ID")
        if st.button("Submit Shopkeeper"):
            query = "INSERT INTO SHOPKEEPER (Shopkeeper_id, S_Fname, S_Lname, Store_name, Street_no, City, PIN, Admin_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
            params = (shopkeeper_id, s_fname, s_lname, store_name, street_no, city, pin, admin_id)
            execute_query(query, params)
            st.success(f"Shopkeeper {s_fname} {s_lname} added successfully!")

    elif operation == "View":
        shopkeepers = fetch_data("SELECT * FROM SHOPKEEPER")
        if shopkeepers:
            df = pd.DataFrame(shopkeepers)
            column_names = {
                'Shopkeeper_id': 'Shopkeeper ID',
                'S_Fname': 'First Name',
                'S_Lname': 'Last Name',
                'Store_name': 'Store Name',
                'Street_no': 'Street No',
                'City': 'City',
                'PIN': 'PIN',
                'Admin_id': 'Admin ID'
            }
            df = df.rename(columns=column_names)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No shopkeeper records found.")

    elif operation == "Edit":
        st.subheader("Edit Shopkeeper")
        shopkeepers = fetch_data("SELECT Shopkeeper_id, S_Fname, S_Lname FROM SHOPKEEPER")
        shopkeeper_options = {f"{shopkeeper['S_Fname']} {shopkeeper['S_Lname']}": shopkeeper['Shopkeeper_id'] for shopkeeper in shopkeepers}
        selected_shopkeeper = st.selectbox("Select Shopkeeper to Edit", options=shopkeeper_options.keys())
        if selected_shopkeeper:
            shopkeeper_id = shopkeeper_options[selected_shopkeeper]
            shopkeeper_data = fetch_data("SELECT * FROM SHOPKEEPER WHERE Shopkeeper_id = %s", (shopkeeper_id,))[0]
            s_fname = st.text_input("First Name", shopkeeper_data["S_Fname"])
            s_lname = st.text_input("Last Name", shopkeeper_data["S_Lname"])
            store_name = st.text_input("Store Name", shopkeeper_data["Store_name"])
            street_no = st.text_input("Street No.", shopkeeper_data["Street_no"])
            city = st.text_input("City", shopkeeper_data["City"])
            pin = st.text_input("PIN", shopkeeper_data["PIN"])
            admin_id = st.text_input("Admin ID", shopkeeper_data["Admin_id"])
            if st.button("Update Shopkeeper"):
                query = "UPDATE SHOPKEEPER SET S_Fname = %s, S_Lname = %s, Store_name = %s, Street_no = %s, City = %s, PIN = %s, Admin_id = %s WHERE Shopkeeper_id = %s"
                params = (s_fname, s_lname, store_name, street_no, city, pin, admin_id, shopkeeper_id)
                execute_query(query, params)
                st.success(f"Shopkeeper {s_fname} {s_lname} updated successfully!")

    elif operation == "Remove":
        st.subheader("Remove Shopkeeper")
        shopkeepers = fetch_data("SELECT Shopkeeper_id, S_Fname, S_Lname FROM SHOPKEEPER")
        shopkeeper_options = {f"{shopkeeper['S_Fname']} {shopkeeper['S_Lname']}": shopkeeper['Shopkeeper_id'] for shopkeeper in shopkeepers}
        selected_shopkeeper = st.selectbox("Select Shopkeeper to Remove", options=shopkeeper_options.keys())
        if selected_shopkeeper:
            shopkeeper_id = shopkeeper_options[selected_shopkeeper]
            associated_bills = fetch_data("SELECT COUNT(*) FROM BILL WHERE Shopkeeper_id = %s", (shopkeeper_id,))
            if associated_bills[0]['COUNT(*)'] > 0:
                st.error("Cannot remove the shopkeeper. There are associated bills.")
            else:
                if st.button(f"Confirm Remove {selected_shopkeeper}"):
                    query = "DELETE FROM SHOPKEEPER WHERE Shopkeeper_id = %s"
                    execute_query(query, (shopkeeper_id,))
                    st.success(f"Shopkeeper {selected_shopkeeper} removed successfully!")

@role_required(['Admin', 'Shopkeeper'])
def customer_operations(operation):
    if operation == "Add":
        st.subheader("Add New Customer")
        rfid = st.number_input("RFID", step=1)
        c_fname = st.text_input("First Name")
        c_lname = st.text_input("Last Name")
        c_email = st.text_input("Email")
        dob = st.date_input("Date of Birth")
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        city = st.text_input("City")
        pin = st.text_input("PIN")
        shopkeeper_id = st.text_input("Shopkeeper ID")
        if st.button("Submit Customer"):
            query = "INSERT INTO CUSTOMER (RFID, C_Fname, C_Lname, C_Email_id, DOB, Gender, City, PIN, Shopkeeper_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
            params = (rfid, c_fname, c_lname, c_email, dob, gender, city, pin, shopkeeper_id)
            execute_query(query, params)
            st.success(f"Customer {c_fname} {c_lname} added successfully!")

    elif operation == "View":
        st.subheader("View Customers")
        customers = fetch_data("SELECT * FROM CUSTOMER")
        if customers:
            df = pd.DataFrame(customers)
            column_names = {
                'RFID': 'RFID',
                'C_Fname': 'First Name',
                'C_Lname': 'Last Name',
                'C_Email_id': 'Email',
                'DOB': 'Date of Birth',
                'Gender': 'Gender',
                'City': 'City',
                'PIN': 'PIN',
                'Shopkeeper_id': 'Shopkeeper ID'
            }
            df = df.rename(columns=column_names)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No customer records found.")

    elif operation == "Edit":
        st.subheader("Edit Customer")
        customers = fetch_data("SELECT RFID, C_Fname, C_Lname FROM CUSTOMER")
        customer_options = {f"{customer['C_Fname']} {customer['C_Lname']}": customer['RFID'] for customer in customers}
        selected_customer = st.selectbox("Select Customer to Edit", options=customer_options.keys())
        if selected_customer:
            rfid = customer_options[selected_customer]
            customer_data = fetch_data("SELECT * FROM CUSTOMER WHERE RFID = %s", (rfid,))[0]
            c_fname = st.text_input("First Name", customer_data["C_Fname"])
            c_lname = st.text_input("Last Name", customer_data["C_Lname"])
            c_email = st.text_input("Email", customer_data["C_Email_id"])
            dob = st.date_input("Date of Birth", customer_data["DOB"])
            gender = st.selectbox("Gender", ["Male", "Female", "Other"], index=["Male", "Female", "Other"].index(customer_data["Gender"]))
            city = st.text_input("City", customer_data["City"])
            pin = st.text_input("PIN", customer_data["PIN"])
            shopkeeper_id = st.text_input("Shopkeeper ID", value=customer_data.get("Shopkeeper_id", ""))
            if st.button("Update Customer"):
                query = "UPDATE CUSTOMER SET C_Fname = %s, C_Lname = %s, C_Email_id = %s, DOB = %s, Gender = %s, City = %s, PIN = %s, Shopkeeper_id = %s WHERE RFID = %s"
                params = (c_fname, c_lname, c_email, dob, gender, city, pin, shopkeeper_id, rfid)
                execute_query(query, params)
                st.success(f"Customer {c_fname} {c_lname} updated successfully!")

    elif operation == "Remove":
        st.subheader("Remove Customer")
        customers = fetch_data("SELECT RFID, C_Fname, C_Lname FROM CUSTOMER")
        customer_options = {f"{customer['C_Fname']} {customer['C_Lname']}": customer['RFID'] for customer in customers}
        selected_customer = st.selectbox("Select Customer to Remove", options=customer_options.keys())
        if selected_customer:
            rfid = customer_options[selected_customer]
            associated_bills = fetch_data("SELECT COUNT(*) FROM BILL WHERE RFID = %s", (rfid,))
            associated_dependents = fetch_data("SELECT COUNT(*) FROM DEPENDENT WHERE RFID = %s", (rfid,))
            
            if associated_bills[0]['COUNT(*)'] > 0 or associated_dependents[0]['COUNT(*)'] > 0:
                st.error("Cannot remove the customer. There are associated bills or dependents.")
            else:
                if st.button(f"Confirm Remove {selected_customer}"):
                    query = "DELETE FROM CUSTOMER WHERE RFID = %s"
                    execute_query(query, (rfid,))
                    st.success(f"Customer {selected_customer} removed successfully!")


@role_required(['Admin', 'Shopkeeper'])
def dependent_operations(operation):
    if operation == "Add":
        st.subheader("Add New Dependent")
        
        try:
            # Create the age validation trigger
            connection = create_connection()
            if connection:
                cursor = connection.cursor()
                try:
                    # Drop existing trigger if it exists
                    cursor.execute("DROP TRIGGER IF EXISTS dependent_age")
                    
                    # Create new trigger as a backup validation
                    create_trigger_query = """
                    CREATE TRIGGER dependent_age
                    BEFORE INSERT ON DEPENDENT
                    FOR EACH ROW
                    BEGIN
                        DECLARE error_msg VARCHAR(300);
                        SET error_msg = 'Age of the dependent should be 10 or more';
                        IF NEW.Age < 10 THEN
                            SIGNAL SQLSTATE '45000'
                            SET MESSAGE_TEXT = error_msg;
                        END IF;
                    END;
                    """
                    cursor.execute(create_trigger_query)
                    connection.commit()
                except Error as e:
                    st.error(f"Error creating trigger: {str(e)}")
                finally:
                    cursor.close()
                    connection.close()

            # Fetch all customers for dropdown
            customers = fetch_data("""
                SELECT RFID, C_Fname, C_Lname, City 
                FROM CUSTOMER 
                ORDER BY C_Fname, C_Lname
            """)
            
            if not customers:
                st.warning("No customers found in the system.")
                return
                
            # Create customer options for dropdown
            customer_options = {
                f"{c['C_Fname']} {c['C_lname']} - {c['City']} (RFID: {c['RFID']})": c['RFID']
                for c in customers
            }
            
            # Dropdown for customer selection
            selected_customer = st.selectbox(
                "Select Customer",
                options=list(customer_options.keys())
            )
            
            rfid = customer_options[selected_customer] if selected_customer else None
            d_name = st.text_input("Dependent Name")
            dob = st.date_input("Date of Birth")
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            age = st.number_input("Age", min_value=1)
            relation = st.text_input("Relation (e.g., Spouse, Child)")

            if st.button("Submit Dependent"):
                # Frontend validation
                if age < 10:
                    st.error("Age of the dependent should be 10 or more")
                elif not rfid:
                    st.error("Please select a customer")
                else:
                    try:
                        query = """
                        INSERT INTO DEPENDENT (RFID, D_Name, DOB, Gender, Age, Relation) 
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """
                        params = (rfid, d_name, dob, gender, age, relation)
                        
                        # Execute the insert query - the trigger serves as a backup validation
                        execute_query(query, params)
                        st.success(f"Dependent {d_name} added successfully for {selected_customer.split(' (RFID')[0]}!")
                    except Error as e:
                        if "Age of the dependent should be 10 or more" in str(e):
                            st.error("Error: Age of the dependent should be 10 or more")
                        else:
                            st.error(f"Error adding dependent: {str(e)}")

        except Exception as e:
            st.error(f"Error in Add operation: {str(e)}")

    elif operation == "View":
        # Fetch all customers for filtering
        customers = fetch_data("""
            SELECT RFID, C_Fname, C_Lname, City 
            FROM CUSTOMER 
            ORDER BY C_Fname, C_Lname
        """)
        
        if customers:
            customer_options = {
                f"{c['C_Fname']} {c['C_lname']} - {c['City']} (RFID: {c['RFID']})": c['RFID']
                for c in customers
            }
            customer_options["All Customers"] = None  # Add option to view all dependents
            
            selected_customer = st.selectbox(
                "Filter by Customer",
                options=list(customer_options.keys())
            )
            
            rfid = customer_options[selected_customer]
            
            if rfid:
                dependents = fetch_data("""
                    SELECT d.*, c.C_Fname, c.C_lname 
                    FROM DEPENDENT d
                    JOIN CUSTOMER c ON d.RFID = c.RFID
                    WHERE d.RFID = %s
                """, (rfid,))
            else:
                dependents = fetch_data("""
                    SELECT d.*, c.C_Fname, c.C_lname 
                    FROM DEPENDENT d
                    JOIN CUSTOMER c ON d.RFID = c.RFID
                """)
            
            if dependents:
                df = pd.DataFrame(dependents)
                column_names = {
                    'RFID': 'Customer RFID',
                    'D_Name': 'Dependent Name',
                    'DOB': 'Date of Birth',
                    'Gender': 'Gender',
                    'Age': 'Age',
                    'Relation': 'Relation',
                    'C_Fname': 'Customer First Name',
                    'C_Lname': 'Customer Last Name'
                }
                df = df.rename(columns=column_names)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No dependent records found.")
        else:
            st.warning("No customers found in the system.")

    elif operation == "Edit":
        st.subheader("Edit Dependent")
        
        # First, select the customer
        customers = fetch_data("""
            SELECT RFID, C_Fname, C_Lname, City 
            FROM CUSTOMER 
            ORDER BY C_Fname, C_Lname
        """)
        
        if not customers:
            st.warning("No customers found in the system.")
            return
            
        customer_options = {
            f"{c['C_Fname']} {c['C_Lname']} - {c['City']} (RFID: {c['RFID']})": c['RFID']
            for c in customers
        }
        
        selected_customer = st.selectbox(
            "Select Customer",
            options=list(customer_options.keys())
        )
        
        if selected_customer:
            rfid = customer_options[selected_customer]
            
            # Fetch dependents for selected customer
            dependents = fetch_data("""
                SELECT * FROM DEPENDENT 
                WHERE RFID = %s
            """, (rfid,))
            
            if not dependents:
                st.info("No dependents found for this customer.")
                return
                
            dependent_options = {
                f"{d['D_Name']} ({d['Relation']})": d['D_Name']
                for d in dependents
            }
            
            selected_dependent = st.selectbox(
                "Select Dependent to Edit",
                options=list(dependent_options.keys())
            )
            
            if selected_dependent:
                d_name = dependent_options[selected_dependent]
                dependent_data = next(d for d in dependents if d['D_Name'] == d_name)
                
                new_d_name = st.text_input("Dependent Name", dependent_data["D_Name"])
                dob = st.date_input("Date of Birth", dependent_data["DOB"])
                gender = st.selectbox("Gender", ["Male", "Female", "Other"], 
                                    index=["Male", "Female", "Other"].index(dependent_data["Gender"]))
                age = st.number_input("Age", value=dependent_data["Age"], min_value=1)
                relation = st.text_input("Relation", dependent_data["Relation"])
                
                if st.button("Update Dependent"):
                    if age < 10:
                        st.error("Age of the dependent should be 10 or more")
                    else:
                        query = """
                        UPDATE DEPENDENT 
                        SET D_Name = %s, DOB = %s, Gender = %s, Age = %s, Relation = %s 
                        WHERE RFID = %s AND D_Name = %s
                        """
                        params = (new_d_name, dob, gender, age, relation, rfid, d_name)
                        execute_query(query, params)
                        st.success(f"Dependent {new_d_name} updated successfully!")

    elif operation == "Remove":
        st.subheader("Remove Dependent")
        
        # First, select the customer
        customers = fetch_data("""
            SELECT RFID, C_Fname, C_Lname, City 
            FROM CUSTOMER 
            ORDER BY C_Fname, C_Lname
        """)
        
        if not customers:
            st.warning("No customers found in the system.")
            return
            
        customer_options = {
            f"{c['C_Fname']} {c['C_lname']} - {c['City']} (RFID: {c['RFID']})": c['RFID']
            for c in customers
        }
        
        selected_customer = st.selectbox(
            "Select Customer",
            options=list(customer_options.keys())
        )
        
        if selected_customer:
            rfid = customer_options[selected_customer]
            
            # Fetch dependents for selected customer
            dependents = fetch_data("""
                SELECT * FROM DEPENDENT 
                WHERE RFID = %s
            """, (rfid,))
            
            if not dependents:
                st.info("No dependents found for this customer.")
                return
                
            dependent_options = {
                f"{d['D_Name']} ({d['Relation']})": d['D_Name']
                for d in dependents
            }
            
            selected_dependent = st.selectbox(
                "Select Dependent to Remove",
                options=list(dependent_options.keys())
            )
            
            if selected_dependent:
                d_name = dependent_options[selected_dependent]
                
                st.warning("⚠️ Are you sure you want to remove this dependent?")
                if st.button("Confirm Remove"):
                    query = "DELETE FROM DEPENDENT WHERE RFID = %s AND D_Name = %s"
                    execute_query(query, (rfid, d_name))
                    st.success(f"Dependent {selected_dependent} removed successfully!")
@role_required(['Admin', 'Shopkeeper'])
def customer_phone_operations(operation):
    def add_customer_phone():
        st.subheader("Add Phone Number to Customer")
        
        # Fetch all customers with their names and RFIDs
        customers = fetch_data("""
            SELECT RFID, C_Fname, C_Lname, City 
            FROM CUSTOMER 
            ORDER BY C_Fname, C_Lname
        """)
        
        if not customers:
            st.warning("No customers found in the system.")
            return
            
        # Create customer options for dropdown
        customer_options = {
            f"{c['C_Fname']} {c['C_Lname']} - {c['City']} (RFID: {c['RFID']})": c['RFID']
            for c in customers
        }
        
        # Dropdown for customer selection
        selected_customer = st.selectbox(
            "Select Customer",
            options=list(customer_options.keys())
        )
        
        rfid = customer_options[selected_customer] if selected_customer else None
        phone_no = st.number_input("Phone Number", step=1)
        
        if st.button("Add Phone Number"):
            query = """
            INSERT INTO CUSTOMER_PHONE (RFID, Phone_no) 
            VALUES (%s, %s)
            """
            params = (rfid, phone_no)
            execute_query(query, params)
            st.success(f"Phone number {phone_no} added to customer {selected_customer}!")

    def view_customer_phone():
        st.subheader("View Phone Numbers for Customer")
        
        # Fetch all customers
        customers = fetch_data("""
            SELECT RFID, C_Fname, C_Lname, City 
            FROM CUSTOMER 
            ORDER BY C_Fname, C_Lname
        """)
        
        if not customers:
            st.warning("No customers found in the system.")
            return
            
        # Create customer options for dropdown
        customer_options = {
            f"{c['C_Fname']} {c['C_lname']} - {c['City']} (RFID: {c['RFID']})": c['RFID']
            for c in customers
        }
        
        # Dropdown for customer selection
        selected_customer = st.selectbox(
            "Select Customer",
            options=list(customer_options.keys())
        )

        if selected_customer:
            rfid = customer_options[selected_customer]
            query = "SELECT Phone_no FROM CUSTOMER_PHONE WHERE RFID = %s"
            params = (rfid,)
            phone_numbers = fetch_data(query, params)

            if phone_numbers:
                st.write(f"Phone Numbers for {selected_customer}:")
                for phone in phone_numbers:
                    st.write(phone['Phone_no'])
            else:
                st.info("No phone numbers found for this customer.")

    def update_customer_phone():
        st.subheader("Update Phone Number for Customer")
        
        # Fetch all customers
        customers = fetch_data("""
            SELECT RFID, C_Fname, C_Lname, City 
            FROM CUSTOMER 
            ORDER BY C_Fname, C_Lname
        """)
        
        if not customers:
            st.warning("No customers found in the system.")
            return
            
        # Create customer options for dropdown
        customer_options = {
            f"{c['C_Fname']} {c['C_lname']} - {c['City']} (RFID: {c['RFID']})": c['RFID']
            for c in customers
        }
        
        # Dropdown for customer selection
        selected_customer = st.selectbox(
            "Select Customer",
            options=list(customer_options.keys())
        )

        if selected_customer:
            rfid = customer_options[selected_customer]
            
            # Fetch existing phone numbers for the selected customer
            existing_phones = fetch_data(
                "SELECT Phone_no FROM CUSTOMER_PHONE WHERE RFID = %s",
                (rfid,)
            )
            
            if not existing_phones:
                st.warning("No phone numbers found for this customer.")
                return
                
            # Create dropdown for existing phone numbers
            phone_options = [phone['Phone_no'] for phone in existing_phones]
            old_phone_no = st.selectbox("Select Phone Number to Update", options=phone_options)
            new_phone_no = st.number_input("New Phone Number", step=1)

            if st.button("Update Phone Number"):
                query = """
                UPDATE CUSTOMER_PHONE 
                SET Phone_no = %s
                WHERE RFID = %s AND Phone_no = %s
                """
                params = (new_phone_no, rfid, old_phone_no)
                execute_query(query, params)
                st.success(f"Phone number for customer {selected_customer} updated to {new_phone_no}!")

    def delete_customer_phone():
        st.subheader("Remove Phone Number from Customer")
        
        # Fetch all customers
        customers = fetch_data("""
            SELECT RFID, C_Fname, C_Lname, City 
            FROM CUSTOMER 
            ORDER BY C_Fname, C_Lname
        """)
        
        if not customers:
            st.warning("No customers found in the system.")
            return
            
        # Create customer options for dropdown
        customer_options = {
            f"{c['C_Fname']} {c['C_lname']} - {c['City']} (RFID: {c['RFID']})": c['RFID']
            for c in customers
        }
        
        # Dropdown for customer selection
        selected_customer = st.selectbox(
            "Select Customer",
            options=list(customer_options.keys())
        )

        if selected_customer:
            rfid = customer_options[selected_customer]
            
            # Fetch existing phone numbers for the selected customer
            existing_phones = fetch_data(
                "SELECT Phone_no FROM CUSTOMER_PHONE WHERE RFID = %s",
                (rfid,)
            )
            
            if not existing_phones:
                st.warning("No phone numbers found for this customer.")
                return
                
            # Create dropdown for existing phone numbers
            phone_options = [phone['Phone_no'] for phone in existing_phones]
            phone_no = st.selectbox("Select Phone Number to Remove", options=phone_options)

            if st.button("Remove Phone Number"):
                query = """
                DELETE FROM CUSTOMER_PHONE 
                WHERE RFID = %s AND Phone_no = %s
                """
                params = (rfid, phone_no)
                execute_query(query, params)
                st.success(f"Phone number {phone_no} removed from customer {selected_customer}!")

    if operation == "Add":
        add_customer_phone()
    elif operation == "View":
        view_customer_phone()
    elif operation == "Edit":
        update_customer_phone()
    elif operation == "Remove":
        delete_customer_phone()


@role_required(['Admin', 'Shopkeeper'])
def shopkeeper_phone_operations(operation):
    def add_shopkeeper_phone():
        st.subheader("Add Phone Number to Shopkeeper")
        shopkeeper_id = st.text_input("Shopkeeper ID", max_chars=10)
        phone_no = st.number_input("Phone Number", step=1)

        if st.button("Add Phone Number"):
            query = """
            INSERT INTO SHOPKEEPER_PHONE (Shopkeeper_id, Phone_no) 
            VALUES (%s, %s)
            """
            params = (shopkeeper_id, phone_no)
            execute_query(query, params)
            st.success(f"Phone number {phone_no} added to shopkeeper {shopkeeper_id}!")

    # CRUD Operation 2: View Phone Numbers for a Shopkeeper
    def view_shopkeeper_phone():
        st.subheader("View Phone Numbers for Shopkeeper")
        shopkeeper_id = st.text_input("Shopkeeper ID", max_chars=10)

        if st.button("View Phone Numbers"):
            query = "SELECT Phone_no FROM SHOPKEEPER_PHONE WHERE Shopkeeper_id = %s"
            params = (shopkeeper_id,)
            phone_numbers = fetch_data(query, params)

            if phone_numbers:
                st.write(f"Phone Numbers for shopkeeper {shopkeeper_id}:")
                for phone in phone_numbers:
                    st.write(phone[0])
            else:
                st.warning("No phone numbers found for this shopkeeper.")

    # CRUD Operation 3: Update Phone Number for a Shopkeeper
    def update_shopkeeper_phone():
        st.subheader("Update Phone Number for Shopkeeper")
        shopkeeper_id = st.text_input("Shopkeeper ID", max_chars=10)
        old_phone_no = st.number_input("Existing Phone Number", step=1)
        new_phone_no = st.number_input("New Phone Number", step=1)

        if st.button("Update Phone Number"):
            query = """
            UPDATE SHOPKEEPER_PHONE 
            SET Phone_no = %s
            WHERE Shopkeeper_id = %s AND Phone_no = %s
            """
            params = (new_phone_no, shopkeeper_id, old_phone_no)
            execute_query(query, params)
            st.success(f"Phone number for shopkeeper {shopkeeper_id} updated to {new_phone_no}!")

    # CRUD Operation 4: Remove Phone Number from a Shopkeeper
    def delete_shopkeeper_phone():
        st.subheader("Remove Phone Number from Shopkeeper")
        shopkeeper_id = st.text_input("Shopkeeper ID", max_chars=10)
        phone_no = st.number_input("Phone Number to Remove", step=1)

        if st.button("Remove Phone Number"):
            query = """
            DELETE FROM SHOPKEEPER_PHONE 
            WHERE Shopkeeper_id = %s AND Phone_no = %s
            """
            params = (shopkeeper_id, phone_no)
            execute_query(query, params)
            st.success(f"Phone number {phone_no} removed from shopkeeper {shopkeeper_id}!")

    if operation == "Add":
        add_shopkeeper_phone()
    elif operation == "View":
        view_shopkeeper_phone()
    elif operation == "Edit":
        update_shopkeeper_phone()
    elif operation == "Remove":
        delete_shopkeeper_phone()

@role_required(['Admin','Shopkeeper'])
def execute_analytical_query(query):
    connection = create_connection()
    if connection is None:
        return None, None
    try:
        cursor = connection.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        cursor.close()
        connection.close()
        return result, columns
    except Error as e:
        st.error(f"Error executing query: {e}")
        return None, None
join_queries = {
    "Inner Join: Customer and Son Details": """
        SELECT C_Fname, C_Lname, D_Name AS Son_Name 
        FROM CUSTOMER 
        JOIN DEPENDENT ON CUSTOMER.RFID = DEPENDENT.RFID 
        WHERE DEPENDENT.Relation = 'Son';
    """,
    
    "Left Join: All Customers with Dependencies": """
        SELECT C_Fname, C_Lname, D_Name 
        FROM CUSTOMER 
        LEFT JOIN DEPENDENT ON CUSTOMER.RFID = DEPENDENT.RFID;
    """,
    
    "Right Join: Dependencies with Customer Details": """
        SELECT D_Name, C_Fname, C_Lname 
        FROM DEPENDENT 
        RIGHT JOIN CUSTOMER ON CUSTOMER.RFID = DEPENDENT.RFID;
    """,
    
    "Multiple Joins: Customer Purchase History": """
        SELECT C_Fname, C_Lname, Present_date AS Bought_date 
        FROM CUSTOMER 
        JOIN BILL ON CUSTOMER.RFID = BILL.RFID 
        WHERE BILL.Present_date BETWEEN '2021-02-28' AND '2021-10-03';
    """
}

set_operations = {
    "Union: All Admin and Shopkeeper Phone Numbers": """
        SELECT ADMIN_PHONE.Phone_no, 'Admin' as Source
        FROM ADMIN_PHONE 
        UNION 
        SELECT SHOPKEEPER_PHONE.Phone_no, 'Shopkeeper' as Source
        FROM SHOPKEEPER_PHONE;
    """,
    
    "Intersect: Common Cities between Customers and Shopkeepers": """
        SELECT S.City 
        FROM SHOPKEEPER S 
        INTERSECT 
        SELECT C.City 
        FROM CUSTOMER C;
    """,
    
    "Union All: All Phone Numbers in System": """
        SELECT Phone_no, 'Customer' as Owner_Type
        FROM CUSTOMER_PHONE
        UNION ALL
        SELECT Phone_no, 'Admin' as Owner_Type
        FROM ADMIN_PHONE
        UNION ALL
        SELECT Phone_no, 'Shopkeeper' as Owner_Type
        FROM SHOPKEEPER_PHONE;
    """
}

aggregate_queries = {
    "Total Amount Spent by Each Customer": """
        SELECT c.RFID, c.C_Fname, c.C_Lname, 
               COUNT(b.Bill_id) as Number_of_Bills,
               SUM(b.Total_cost) as Total_Spent,
               AVG(b.Total_cost) as Average_Bill_Amount
        FROM CUSTOMER c
        JOIN BILL b ON c.RFID = b.RFID 
        GROUP BY c.RFID, c.C_Fname, c.C_Lname;
    """,
    
    "Maximum and Minimum Bill Details": """
        SELECT 
            MAX(Total_cost) as Highest_Bill,
            MIN(Total_cost) as Lowest_Bill,
            AVG(Total_cost) as Average_Bill,
            COUNT(*) as Total_Bills,
            SUM(Total_cost) as Total_Revenue
        FROM BILL;
    """,
    
    "Customer Purchase Statistics by City": """
        SELECT 
            c.City,
            COUNT(DISTINCT c.RFID) as Number_of_Customers,
            COUNT(b.Bill_id) as Total_Bills,
            AVG(b.Total_cost) as Average_Bill_Amount,
            MAX(b.Total_cost) as Highest_Bill,
            SUM(b.Total_cost) as Total_Revenue
        FROM CUSTOMER c
        JOIN BILL b ON c.RFID = b.RFID
        GROUP BY c.City;
    """,
    
    "Dependents per Customer Count": """
        SELECT 
            c.RFID,
            c.C_Fname,
            c.C_Lname,
            COUNT(d.D_Name) as Number_of_Dependents
        FROM CUSTOMER c
        LEFT JOIN DEPENDENT d ON c.RFID = d.RFID
        GROUP BY c.RFID, c.C_Fname, c.C_Lname;
    """
}

nested_queries = {
    "Customers with Above Average Spending": """
        WITH AverageBill AS (
            SELECT AVG(Total_cost) as avg_bill
            FROM BILL
        )
        SELECT 
            c.RFID,
            c.C_Fname as First_Name,
            c.C_Lname as Last_Name,
            c.City,
            b.Bill_id,
            ROUND(b.Total_cost, 2) as Bill_Amount,
            ROUND((SELECT avg_bill FROM AverageBill), 2) as Average_Bill_Amount,
            ROUND(b.Total_cost - (SELECT avg_bill FROM AverageBill), 2) as Amount_Above_Average
        FROM 
            CUSTOMER c
            JOIN BILL b ON c.RFID = b.RFID
            CROSS JOIN AverageBill
        WHERE 
            b.Total_cost > (SELECT avg_bill FROM AverageBill)
        ORDER BY 
            b.Total_cost DESC;
    """,
    
    "Customers with Maximum Dependents": """
        SELECT c.RFID, c.C_Fname, c.C_lname, dep_count.dependent_count
        FROM CUSTOMER c
        JOIN (
            SELECT RFID, COUNT(*) as dependent_count
            FROM DEPENDENT
            GROUP BY RFID
            HAVING COUNT(*) = (
                SELECT COUNT(*)
                FROM DEPENDENT
                GROUP BY RFID
                ORDER BY COUNT(*) DESC
                LIMIT 1
            )
        ) dep_count ON c.RFID = dep_count.RFID;
    """,
    
    "Shopkeepers with Highest Sales in Their City": """
        SELECT s.Shopkeeper_id, s.S_Fname, s.S_lname, s.City, 
               SUM(b.Total_cost) as Total_Sales
        FROM SHOPKEEPER s
        JOIN BILL b ON s.Shopkeeper_id = b.Shopkeeper_id
        GROUP BY s.Shopkeeper_id, s.City
        HAVING SUM(b.Total_cost) >= ALL (
            SELECT SUM(b2.Total_cost)
            FROM BILL b2
            JOIN SHOPKEEPER s2 ON b2.Shopkeeper_id = s2.Shopkeeper_id
            WHERE s2.City = s.City
            GROUP BY s2.Shopkeeper_id
        )
        ORDER BY Total_Sales DESC;
    """
}    
@role_required(['Admin','Shopkeeper'])
def queries_section():
    st.subheader("SQL Analytics")
    
    # Create tabs for different query categories
    query_type = st.selectbox(
        "Select Query Type",
        ["Join Queries", "Set Operations", "Aggregate Functions", "Nested Queries"]
    )
    
    # Show appropriate queries based on selection
    if query_type == "Join Queries":
        selected_query = st.selectbox('Select Join Query', list(join_queries.keys()))
        query_dict = join_queries
    elif query_type == "Set Operations":
        selected_query = st.selectbox('Select Set Operation', list(set_operations.keys()))
        query_dict = set_operations
    elif query_type == "Aggregate Functions":
        selected_query = st.selectbox('Select Aggregate Query', list(aggregate_queries.keys()))
        query_dict = aggregate_queries
    else:  # Nested Queries
        selected_query = st.selectbox('Select Nested Query', list(nested_queries.keys()))
        query_dict = nested_queries

    if st.button('Execute Query'):
        results, columns = execute_analytical_query(query_dict[selected_query])
        if results and columns:
            df = pd.DataFrame(results, columns=columns)
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("No results found")
@role_required(['Admin','Shopkeeper'])
def execute_analytical_query(query):
    connection = create_connection()
    if connection is None:
        return None, None
    try:
        cursor = connection.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        cursor.close()
        connection.close()
        return result, columns
    except Error as e:
        st.error(f"Error executing query: {e}")
        return None, None
@role_required(['Admin','Shopkeeper'])
def queries_section():
    st.subheader("SQL Analytics")
    
    # Create tabs for different query categories
    query_type = st.selectbox(
        "Select Query Type",
        ["Join Queries", "Set Operations", "Aggregate Functions", "Nested Queries"]
    )
    
    # Show appropriate queries based on selection
    if query_type == "Join Queries":
        selected_query = st.selectbox('Select Join Query', list(join_queries.keys()))
        query_dict = join_queries
    elif query_type == "Set Operations":
        selected_query = st.selectbox('Select Set Operation', list(set_operations.keys()))
        query_dict = set_operations
    elif query_type == "Aggregate Functions":
        selected_query = st.selectbox('Select Aggregate Query', list(aggregate_queries.keys()))
        query_dict = aggregate_queries
    else:  # Nested Queries
        selected_query = st.selectbox('Select Nested Query', list(nested_queries.keys()))
        query_dict = nested_queries

    if st.button('Execute Query'):
        results, columns = execute_analytical_query(query_dict[selected_query])
        if results and columns:
            df = pd.DataFrame(results, columns=columns)
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("No results found")




@role_required(['Admin', 'Shopkeeper'])
def bill_operations(operation):
    shopkeeper_id = st.session_state.username
    st.write(f"Debug: Current operation - {operation}")
    st.write(f"Debug: Shopkeeper ID - {shopkeeper_id}")

    if operation == "Add":
        st.subheader("Add New Bill")
        
        try:
            # Get all customers
            customers = fetch_data("""
                SELECT RFID, C_Fname, C_Lname, City 
                FROM CUSTOMER
            """)
            
            if not customers:
                st.warning("No customers found in the system.")
                return

            # Form Layout
            col1, col2 = st.columns(2)
            
            with col1:
                bill_id = st.text_input("Bill ID", max_chars=10)
                total_cost = st.number_input("Total Cost (₹)", 
                                           min_value=0.0, 
                                           step=0.01, 
                                           format="%.2f")
                issued_date = st.date_input("Issued Date")
                
            with col2:
                last_valid_date = st.date_input("Last Valid Date")
                present_date = st.date_input("Present Date")
                # Validity will be automatically set by the trigger
                validity = "Valid"  # Default value

            # Customer selection
            customer_options = {
                f"{c['C_Fname']} {c['C_Lname']} - {c['City']} (RFID: {c['RFID']})": c['RFID']
                for c in customers
            }
            selected_customer = st.selectbox(
                "Select Customer",
                options=list(customer_options.keys())
            )

            if st.button("Submit Bill"):
                if not bill_id:
                    st.error("Bill ID is required")
                    return

                try:
                    # Check if bill_id already exists
                    existing_bill = fetch_data(
                        "SELECT Bill_id FROM BILL WHERE Bill_id = %s",
                        (bill_id,)
                    )
                    
                    if existing_bill:
                        st.error("This Bill ID already exists. Please use a different ID.")
                        return
                    
                    rfid = customer_options[selected_customer]
                    
                    # Create the trigger if it doesn't exist
                    connection = create_connection()
                    if connection:
                        cursor = connection.cursor()
                        try:
                            # Drop existing trigger if it exists
                            cursor.execute("DROP TRIGGER IF EXISTS buying_date")
                            
                            # Create new trigger
                            create_trigger_query = """
                            CREATE TRIGGER buying_date
                            BEFORE INSERT ON BILL
                            FOR EACH ROW
                            BEGIN
                                IF NEW.Present_date > NEW.Last_valid_date THEN 
                                    SET NEW.Validity = 'Invalid';
                                END IF;
                            END;
                            """
                            cursor.execute(create_trigger_query)
                            connection.commit()
                        except Error as e:
                            st.error(f"Error creating trigger: {str(e)}")
                        finally:
                            cursor.close()
                            connection.close()
                    
                    # Insert the bill (trigger will automatically set validity)
                    query = """
                    INSERT INTO BILL (
                        Bill_id, Total_cost, Issued_date, Last_valid_date, 
                        Present_date, Validity, Shopkeeper_id, RFID
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    params = (
                        bill_id, total_cost, issued_date, last_valid_date,
                        present_date, validity, shopkeeper_id, rfid
                    )
                    
                    execute_query(query, params)
                    
                    # Fetch the updated bill to show correct validity
                    updated_bill = fetch_data(
                        "SELECT * FROM BILL WHERE Bill_id = %s",
                        (bill_id,)
                    )[0]
                    
                    st.success(f"Bill {bill_id} created successfully!")
                    st.write("Bill Details:")
                    st.json({
                        "Bill ID": bill_id,
                        "Customer": selected_customer.split(" (RFID")[0],
                        "Amount": f"₹{total_cost:.2f}",
                        "Issued Date": issued_date.strftime("%Y-%m-%d"),
                        "Valid Until": last_valid_date.strftime("%Y-%m-%d"),
                        "Present Date": present_date.strftime("%Y-%m-%d"),
                        "Status": updated_bill['Validity']  # Show the trigger-updated validity
                    })
                    
                except Exception as e:
                    st.error(f"Error creating bill: {str(e)}")
                    
        except Exception as e:
            st.error(f"Error in Add operation: {str(e)}")

    elif operation == "View":
        st.subheader("View Bills")
        try:
            bills = fetch_data("""
                SELECT 
                    b.*,
                    c.C_Fname,
                    c.C_lname,
                    c.City
                FROM 
                    BILL b
                    JOIN CUSTOMER c ON b.RFID = c.RFID
                WHERE 
                    b.Shopkeeper_id = %s
                ORDER BY 
                    b.Issued_date DESC
            """, (shopkeeper_id,))
            
            if bills:
                # Convert to DataFrame and format
                df = pd.DataFrame(bills)
                
                # Format currency and dates
                df['Total_cost'] = df['Total_cost'].apply(lambda x: f"₹{float(x):,.2f}")
                df['Issued_date'] = pd.to_datetime(df['Issued_date']).dt.strftime('%Y-%m-%d')
                df['Last_valid_date'] = pd.to_datetime(df['Last_valid_date']).dt.strftime('%Y-%m-%d')
                df['Present_date'] = pd.to_datetime(df['Present_date']).dt.strftime('%Y-%m-%d')
                
                # Rename columns
                df = df.rename(columns={
                    'Bill_id': 'Bill ID',
                    'Total_cost': 'Amount',
                    'Issued_date': 'Issued Date',
                    'Last_valid_date': 'Valid Until',
                    'Present_date': 'Present Date',
                    'Validity': 'Status',
                    'C_Fname': 'Customer First Name',
                    'C_lname': 'Customer Last Name',
                    'City': 'City'
                })
                
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Calculate totals
                total_amount = sum(float(str(b['Total_cost']).replace('₹', '').replace(',', '')) for b in bills)
                st.info(f"""
                Summary:
                - Total Bills: {len(bills)}
                - Total Amount: ₹{total_amount:,.2f}
                """)
            else:
                st.info("No bills found.")
                
        except Exception as e:
            st.error(f"Error viewing bills: {str(e)}")

    elif operation == "Edit":
        st.subheader("Edit Bill")
        try:
            bills = fetch_data("""
                SELECT 
                    b.*,
                    c.C_Fname,
                    c.C_lname
                FROM 
                    BILL b
                    JOIN CUSTOMER c ON b.RFID = c.RFID
                WHERE 
                    b.Shopkeeper_id = %s
                ORDER BY 
                    b.Issued_date DESC
            """, (shopkeeper_id,))
            
            if not bills:
                st.info("No bills found to edit.")
                return
            
            bill_options = {
                f"Bill {b['Bill_id']} - {b['C_Fname']} {b['C_lname']} (₹{float(b['Total_cost']):,.2f})": b['Bill_id']
                for b in bills
            }
            
            selected_bill = st.selectbox("Select Bill to Edit", options=list(bill_options.keys()))
            
            if selected_bill:
                bill_id = bill_options[selected_bill]
                current_bill = next(b for b in bills if b['Bill_id'] == bill_id)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    new_total_cost = st.number_input(
                        "Total Cost (₹)", 
                        value=float(current_bill['Total_cost']),
                        min_value=0.0,
                        step=0.01,
                        format="%.2f"
                    )
                    new_issued_date = st.date_input(
                        "Issued Date",
                        value=current_bill['Issued_date']
                    )
                
                with col2:
                    new_last_valid_date = st.date_input(
                        "Last Valid Date",
                        value=current_bill['Last_valid_date']
                    )
                    new_present_date = st.date_input(
                        "Present Date",
                        value=current_bill['Present_date']
                    )
                    new_validity = st.selectbox(
                        "Status",
                        options=["Valid", "Invalid", "Expired"],
                        index=["Valid", "Invalid", "Expired"].index(current_bill['Validity'])
                    )
                
                if st.button("Update Bill"):
                    try:
                        query = """
                        UPDATE BILL 
                        SET Total_cost = %s,
                            Issued_date = %s,
                            Last_valid_date = %s,
                            Present_date = %s,
                            Validity = %s
                        WHERE Bill_id = %s AND Shopkeeper_id = %s
                        """
                        params = (
                            new_total_cost, new_issued_date, new_last_valid_date,
                            new_present_date, new_validity, bill_id, shopkeeper_id
                        )
                        execute_query(query, params)
                        st.success(f"Bill {bill_id} updated successfully!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Error updating bill: {str(e)}")
                        
        except Exception as e:
            st.error(f"Error in Edit operation: {str(e)}")

    elif operation == "Remove":
        st.subheader("Remove Bill")
        try:
            bills = fetch_data("""
                SELECT 
                    b.*,
                    c.C_Fname,
                    c.C_lname
                FROM 
                    BILL b
                    JOIN CUSTOMER c ON b.RFID = c.RFID
                WHERE 
                    b.Shopkeeper_id = %s
                ORDER BY 
                    b.Issued_date DESC
            """, (shopkeeper_id,))
            
            if not bills:
                st.info("No bills found to remove.")
                return
            
            bill_options = {
                f"Bill {b['Bill_id']} - {b['C_Fname']} {b['C_lname']} (₹{float(b['Total_cost']):,.2f})": b['Bill_id']
                for b in bills
            }
            
            selected_bill = st.selectbox("Select Bill to Remove", options=list(bill_options.keys()))
            
            if selected_bill:
                bill_id = bill_options[selected_bill]
                bill_details = next(b for b in bills if b['Bill_id'] == bill_id)
                
                st.warning("⚠️ Are you sure you want to delete this bill? This action cannot be undone.")
                st.write("Bill Details:")
                st.json({
                    "Bill ID": bill_id,
                    "Customer": f"{bill_details['C_Fname']} {bill_details['C_lname']}",
                    "Amount": f"₹{float(bill_details['Total_cost']):,.2f}",
                    "Issued Date": bill_details['Issued_date'].strftime('%Y-%m-%d'),
                    "Status": bill_details['Validity']
                })
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("⚠️ Yes, Delete Bill"):
                        try:
                            query = "DELETE FROM BILL WHERE Bill_id = %s AND Shopkeeper_id = %s"
                            execute_query(query, (bill_id, shopkeeper_id))
                            st.success(f"Bill {bill_id} deleted successfully!")
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"Error deleting bill: {str(e)}")
                            
                with col2:
                    if st.button("Cancel"):
                        st.rerun()
                        
        except Exception as e:
            st.error(f"Error in Remove operation: {str(e)}")

@role_required(['Admin', 'Shopkeeper'])
def sell_operations():
    st.subheader("Ration Card System")
    shopkeeper_id = st.session_state.username

    try:
        col1, col2 = st.columns(2)

        with col1:
            bill_id = st.text_input("Bill ID")
            # Fetch all customers with their details
            customers = fetch_data("""
                SELECT RFID, C_Fname, C_Lname, City 
                FROM CUSTOMER 
                ORDER BY C_Fname, C_Lname
            """)
            
            if not customers:
                st.warning("No customers found in the system.")
                return
                
            # Create customer options for dropdown
            customer_options = {
                f"{c['C_Fname']} {c['C_Lname']} - {c['City']} (RFID: {c['RFID']})": c['RFID']
                for c in customers
            }
            
            # Dropdown for customer selection
            selected_customer = st.selectbox(
                "Select Customer",
                options=list(customer_options.keys())
            )
            rfid = customer_options[selected_customer] if selected_customer else None

        with col2:
            shopkeeper_id_display = st.text_input("Shopkeeper ID", value=shopkeeper_id, disabled=True)

        col1, col2 = st.columns(2)

        with col1:
            issued_date = st.date_input("Issued Date")
            last_valid_date = st.date_input("Last Valid Date")

        with col2:
            present_date = st.date_input("Present Date")
            validity = st.selectbox("Validity", ["Valid", "Invalid", "Expired"])

        # Get all products
        products = fetch_data("SELECT P_Name, Cost_per_unit, Unit FROM PRODUCT")
        if not products:
            st.warning("No products found in the system.")
            return

        # Product selection
        product_options = {p['P_Name']: p for p in products}
        selected_products = st.multiselect("Select Products", options=list(product_options.keys()))

        # Quantity input for each selected product
        quantities = {}
        for product in selected_products:
            quantities[product] = st.number_input(f"Quantity for {product}", min_value=1, value=1)

        if st.button("Create Bill"):
            if not bill_id:
                st.error("Bill ID is required")
                return

            if not rfid:
                st.error("Please select a customer")
                return

            try:
                # Check if bill_id already exists
                existing_bill = fetch_data(
                    "SELECT Bill_id FROM BILL WHERE Bill_id = %s",
                    (bill_id,)
                )

                if existing_bill:
                    st.error("This Bill ID already exists. Please use a different ID.")
                    return

                # Calculate total cost
                total_cost = sum(
                    quantities[product] * product_options[product]['Cost_per_unit']
                    for product in selected_products
                )

                # Insert bill into the database
                query = """
                INSERT INTO BILL (
                    Bill_id, Total_cost, Issued_date, Last_valid_date, 
                    Present_date, Validity, Shopkeeper_id, RFID
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                params = (
                    bill_id, total_cost, issued_date, last_valid_date,
                    present_date, validity, shopkeeper_id, rfid
                )

                execute_query(query, params)

                # Show bill details
                st.success(f"Bill {bill_id} created successfully!")
                st.write("Bill Details:")
                st.json({
                    "Bill ID": bill_id,
                    "Customer": selected_customer.split(" (RFID:")[0],
                    "Products": [
                        {
                            "Name": product,
                            "Quantity": quantities[product],
                            "Cost per Unit": product_options[product]['Cost_per_unit'],
                            "Total Cost": quantities[product] * product_options[product]['Cost_per_unit']
                        }
                        for product in selected_products
                    ],
                    "Total Amount": f"₹{total_cost:.2f}",
                    "Issued Date": issued_date.strftime("%Y-%m-%d"),
                    "Valid Until": last_valid_date.strftime("%Y-%m-%d"),
                    "Status": validity
                })

            except Exception as e:
                st.error(f"Error creating bill: {str(e)}")

    except Exception as e:
        st.error(f"Error in Sell operation: {str(e)}")

@role_required(['Shopkeeper'])
def shopkeeper_product_operations(operation):
    if operation == "Add":
        shopkeeper_id = st.text_input("Shopkeeper ID")
        p_name = st.selectbox("Product Name", [p['P_Name'] for p in fetch_data("SELECT P_Name FROM PRODUCT")])
        if st.button("Add Shopkeeper-Product"):
            execute_query("INSERT INTO SHOPKEEPER_PRODUCT (Shopkeeper_id, P_Name) VALUES (%s, %s)", (shopkeeper_id, p_name))
            st.success(f"Shopkeeper-Product added successfully!")

    elif operation == "View":
        results = fetch_data("SELECT * FROM SHOPKEEPER_PRODUCT")
        st.table(results)

    elif operation == "Edit":
        shopkeeper_id = st.text_input("Shopkeeper ID")
        current_p_name = st.selectbox("Current Product Name", [p['P_Name'] for p in fetch_data("SELECT P_Name FROM SHOPKEEPER_PRODUCT WHERE Shopkeeper_id = %s", (shopkeeper_id,))])
        new_p_name = st.selectbox("New Product Name", [p['P_Name'] for p in fetch_data("SELECT P_Name FROM PRODUCT")])
        if st.button("Update Shopkeeper-Product"):
            execute_query("UPDATE SHOPKEEPER_PRODUCT SET P_Name = %s WHERE Shopkeeper_id = %s AND P_Name = %s", (new_p_name, shopkeeper_id, current_p_name))
            st.success(f"Shopkeeper-Product updated successfully!")

    elif operation == "Remove":
        shopkeeper_id = st.text_input("Shopkeeper ID")
        p_name = st.selectbox("Product Name", [p['P_Name'] for p in fetch_data("SELECT P_Name FROM SHOPKEEPER_PRODUCT WHERE Shopkeeper_id = %s", (shopkeeper_id,))])
        if st.button("Remove Shopkeeper-Product"):
            execute_query("DELETE FROM SHOPKEEPER_PRODUCT WHERE Shopkeeper_id = %s AND P_Name = %s", (shopkeeper_id, p_name))
            st.success(f"Shopkeeper-Product removed successfully!")

@role_required(['Shopkeeper'])
def bill_product_operations(operation):
    if operation == "Add":
        bill_id = st.text_input("Bill ID")
        p_name = st.selectbox("Product Name", [p['P_Name'] for p in fetch_data("SELECT P_Name FROM PRODUCT")])
        quantity = st.number_input("Quantity", min_value=0.0, step=0.1)
        total_cost_per_product = st.number_input("Total Cost per Product", min_value=0.0, step=0.1)
        if st.button("Add Bill-Product"):
            execute_query("INSERT INTO BILL_PRODUCT (Bill_id, P_Name, Quantity, Total_cost_per_product) VALUES (%s, %s, %s, %s)",
                          (bill_id, p_name, quantity, total_cost_per_product))
            st.success(f"Bill-Product added successfully!")

    elif operation == "View":
        results = fetch_data("SELECT * FROM BILL_PRODUCT")
        st.table(results)

    elif operation == "Edit":
        bill_id = st.text_input("Bill ID")
        current_p_name = st.selectbox("Current Product Name", [p['P_Name'] for p in fetch_data("SELECT P_Name FROM BILL_PRODUCT WHERE Bill_id = %s", (bill_id,))])
        new_p_name = st.selectbox("New Product Name", [p['P_Name'] for p in fetch_data("SELECT P_Name FROM PRODUCT")])
        quantity = st.number_input("Quantity", min_value=0.0, step=0.1)
        total_cost_per_product = st.number_input("Total Cost per Product", min_value=0.0, step=0.1)
        if st.button("Update Bill-Product"):
            execute_query("UPDATE BILL_PRODUCT SET P_Name = %s, Quantity = %s, Total_cost_per_product = %s WHERE Bill_id = %s AND P_Name = %s",
                          (new_p_name, quantity, total_cost_per_product, bill_id, current_p_name))
            st.success(f"Bill-Product updated successfully!")

    elif operation == "Remove":
        bill_id = st.text_input("Bill ID")
        p_name = st.selectbox("Product Name", [p['P_Name'] for p in fetch_data("SELECT P_Name FROM BILL_PRODUCT WHERE Bill_id = %s", (bill_id,))])
        if st.button("Remove Bill-Product"):
            execute_query("DELETE FROM BILL_PRODUCT WHERE Bill_id = %s AND P_Name = %s", (bill_id, p_name))
            st.success(f"Bill-Product removed successfully!")
@role_required(['Admin'])
def product_operations(operation):
    if operation == "Add":
        st.subheader("Add New Product")
        
        # Input fields
        p_name = st.text_input("Product Name")
        cost_per_unit = st.number_input(
            "Cost per Unit (₹)", 
            min_value=0.0, 
            max_value=10000.0, 
            step=0.01,
            format="%.2f"
        )
        unit = st.selectbox(
            "Unit",
            options=["Kg", "Liter", "Piece", "Gram", "Packet"]
        )
        
        if st.button("Add Product"):
            if not p_name:
                st.error("Product Name is required")
                return
                
            # Check if product already exists
            existing_product = fetch_data(
                "SELECT P_Name FROM PRODUCT WHERE P_Name = %s",
                (p_name,)
            )
            
            if existing_product:
                st.error("A product with this name already exists")
                return
                
            try:
                query = """
                INSERT INTO PRODUCT (P_Name, Cost_per_unit, Unit) 
                VALUES (%s, %s, %s)
                """
                params = (p_name, cost_per_unit, unit)
                execute_query(query, params)
                st.success(f"Product {p_name} added successfully!")
                
            except Exception as e:
                st.error(f"Error adding product: {str(e)}")

    elif operation == "View":
        st.subheader("View Products")
        
        try:
            products = fetch_data("SELECT * FROM PRODUCT ORDER BY P_Name")
            
            if products:
                # Convert to DataFrame and format
                df = pd.DataFrame(products)
                
                # Format currency
                df['Cost_per_unit'] = df['Cost_per_unit'].apply(lambda x: f"₹{float(x):,.2f}")
                
                # Rename columns
                df = df.rename(columns={
                    'P_Name': 'Product Name',
                    'Cost_per_unit': 'Cost per Unit',
                    'Unit': 'Unit'
                })
                
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Show summary
                st.info(f"""
                Summary:
                - Total Products: {len(products)}
                - Available Units: {', '.join(sorted(set(p['Unit'] for p in products)))}
                """)
            else:
                st.info("No products found in the system.")
                
        except Exception as e:
            st.error(f"Error viewing products: {str(e)}")

    elif operation == "Edit":
        st.subheader("Edit Product")
        
        try:
            # Fetch all products for dropdown
            products = fetch_data("SELECT * FROM PRODUCT ORDER BY P_Name")
            
            if not products:
                st.warning("No products found in the system.")
                return
                
            # Create dropdown options
            product_options = {
                f"{p['P_Name']} ({p['Unit']}) - ₹{float(p['Cost_per_unit']):,.2f}": p['P_Name']
                for p in products
            }
            
            selected_product = st.selectbox(
                "Select Product to Edit",
                options=list(product_options.keys())
            )
            
            if selected_product:
                p_name = product_options[selected_product]
                product_data = next(p for p in products if p['P_Name'] == p_name)
                
                new_cost = st.number_input(
                    "New Cost per Unit (₹)",
                    value=float(product_data['Cost_per_unit']),
                    min_value=0.0,
                    max_value=10000.0,
                    step=0.01,
                    format="%.2f"
                )
                
                new_unit = st.selectbox(
                    "New Unit",
                    options=["Kg", "Liter", "Piece", "Gram", "Packet"],
                    index=["Kg", "Liter", "Piece", "Gram", "Packet"].index(product_data['Unit'])
                )
                
                if st.button("Update Product"):
                    query = """
                    UPDATE PRODUCT 
                    SET Cost_per_unit = %s, Unit = %s
                    WHERE P_Name = %s
                    """
                    params = (new_cost, new_unit, p_name)
                    execute_query(query, params)
                    st.success(f"Product {p_name} updated successfully!")
                    st.rerun()
                    
        except Exception as e:
            st.error(f"Error in Edit operation: {str(e)}")

    elif operation == "Remove":
        st.subheader("Remove Product")
        
        try:
            # Fetch all products for dropdown
            products = fetch_data("SELECT * FROM PRODUCT ORDER BY P_Name")
            
            if not products:
                st.warning("No products found in the system.")
                return
                
            # Create dropdown options
            product_options = {
                f"{p['P_Name']} ({p['Unit']}) - ₹{float(p['Cost_per_unit']):,.2f}": p['P_Name']
                for p in products
            }
            
            selected_product = st.selectbox(
                "Select Product to Remove",
                options=list(product_options.keys())
            )
            
            if selected_product:
                p_name = product_options[selected_product]
                product_data = next(p for p in products if p['P_Name'] == p_name)
                
                st.warning("⚠️ Are you sure you want to delete this product? This action cannot be undone.")
                st.write("Product Details:")
                st.json({
                    "Product Name": p_name,
                    "Cost per Unit": f"₹{float(product_data['Cost_per_unit']):,.2f}",
                    "Unit": product_data['Unit']
                })
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("⚠️ Yes, Delete Product"):
                        try:
                            query = "DELETE FROM PRODUCT WHERE P_Name = %s"
                            execute_query(query, (p_name,))
                            st.success(f"Product {p_name} deleted successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting product: {str(e)}")
                with col2:
                    if st.button("Cancel"):
                        st.rerun()
                        
        except Exception as e:
            st.error(f"Error in Remove operation: {str(e)}")            


@role_required(['Shopkeeper'])
def product_customer_operations(operation):
    if operation == "Add":
        p_name = st.selectbox("Product Name", [p['P_Name'] for p in fetch_data("SELECT P_Name FROM PRODUCT")])
        rfid = st.number_input("RFID", min_value=0, step=1)
        if st.button("Add Product-Customer"):
            execute_query("INSERT INTO PRODUCT_CUSTOMER (P_Name, RFID) VALUES (%s, %s)", (p_name, rfid))
            st.success(f"Product-Customer added successfully!")

    elif operation == "View":
        results = fetch_data("SELECT * FROM PRODUCT_CUSTOMER")
        st.table(results)

    elif operation == "Edit":
        current_p_name = st.selectbox("Current Product Name", [p['P_Name'] for p in fetch_data("SELECT P_Name FROM PRODUCT_CUSTOMER")])
        current_rfid = st.number_input("Current RFID", min_value=0, step=1)
        new_p_name = st.selectbox("New Product Name", [p['P_Name'] for p in fetch_data("SELECT P_Name FROM PRODUCT")])
        new_rfid = st.number_input("New RFID", min_value=0, step=1)
        if st.button("Update Product-Customer"):
            execute_query("UPDATE PRODUCT_CUSTOMER SET P_Name = %s, RFID = %s WHERE P_Name = %s AND RFID = %s",
                          (new_p_name, new_rfid, current_p_name, current_rfid))
            st.success(f"Product-Customer updated successfully!")

    elif operation == "Remove":
        p_name = st.selectbox("Product Name", [p['P_Name'] for p in fetch_data("SELECT P_Name FROM PRODUCT_CUSTOMER")])
        rfid = st.number_input("RFID", min_value=0, step=1)
        if st.button("Remove Product-Customer"):
            execute_query("DELETE FROM PRODUCT_CUSTOMER WHERE P_Name = %s AND RFID = %s", (p_name, rfid))
            st.success(f"Product-Customer removed successfully!")               


# Main Streamlit app with authentication
# Main application section
def main():
    st.set_page_config(page_title="Ration Card Management System", layout="wide")
    
    if not st.session_state.authenticated:
        login_form()
    else:
        # Sidebar navigation
        with st.sidebar:
            st.write(f"Logged in as: {st.session_state.username}")
            st.write(f"Role: {st.session_state.user_role}")
            
            if st.button("Logout"):
                logout()

            # Define menu options based on role
            menu_options = []
            if st.session_state.user_role == 'Admin':
                menu_options = [ "Shopkeeper", "Customer",'Product', "Dependent", 
                              "Customer Phone", "Shopkeeper Phone", "Queries"]
            elif st.session_state.user_role == 'Shopkeeper':
                menu_options = ["Bill", "Sell", "Shopkeeper Product", "Bill Product", "Product Customer","Queries"]

            # Select module
            choice = st.selectbox("Select Module", menu_options)

            # Define operations if not in Queries or Sell section
            operation = None
            if choice not in ["Queries", "Sell"]:
                operations = ["Add", "View", "Edit", "Remove"]
                operation = st.radio("Operation", operations)

        # Main content area
        st.title("Retail Chain Management System")
        
        if choice:
            if choice == "Queries" and st.session_state.user_role == 'Admin':
                queries_section()
            else:
                st.header(f"{choice} Management")
                # Route to appropriate operation based on choice
                if choice == "Admin" and st.session_state.user_role == ['Admin','Shopkeeper']:
                    admin_operations(operation)
                elif choice == "Shopkeeper" and st.session_state.user_role == 'Admin':
                    shopkeeper_operations(operation)
                elif choice == "Customer":
                    customer_operations(operation)
                elif choice == "Dependent":
                    dependent_operations(operation)
                elif choice == "Customer Phone":
                    customer_phone_operations(operation)
                elif choice == "Shopkeeper Phone":
                    shopkeeper_phone_operations(operation)
                elif choice == "Bill" and st.session_state.user_role == 'Shopkeeper':
                    bill_operations(operation)
                elif choice == "Sell":
                    sell_operations()
                elif choice == "Shopkeeper Product":
                    shopkeeper_product_operations(operation)
                elif choice == "Bill Product":
                    bill_product_operations(operation)
                elif choice == "Product Customer":
                    product_customer_operations(operation)
                elif choice == "Product" and st.session_state.user_role == 'Admin':  # Added Product routing
                    product_operations(operation)    

if __name__ == "__main__":
    main()
