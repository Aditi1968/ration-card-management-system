# 🍚 Ration Card Management System (RCMS)

A **Streamlit + MySQL** based project that manages ration card operations.  
This project demonstrates core **DBMS concepts** like **CRUD operations, triggers, joins, aggregates, nested queries, and role-based authentication** — all integrated with an interactive frontend.

---

## 🚀 Features

- **Authentication & Roles**
  - Admin, Shopkeeper, and Customer logins
  - Role-based access control

- **Admin**
  - Manage Admins, Shopkeepers, and Customers

- **Shopkeeper**
  - Manage Customers, Dependents, and Bills

- **Customer**
  - View Bills and Dependents

- **Database**
  - Trigger: validates dependent age ≥ 10 years
  - Trigger: bill validity checks
  - Rich queries: joins, aggregates, nested queries

---

## 🛠️ Tech Stack

- **Frontend:** [Streamlit](https://streamlit.io/)  
- **Backend:** Python 3.12  
- **Database:** MySQL 8.0  
- **Libraries:** `streamlit`, `mysql-connector-python`, `pandas`

---

## ⚙️ Setup Instructions

### 1️⃣ Clone this repository
```bash
git clone https://github.com/your-username/ration-card-management-system.git
cd ration-card-management-system
