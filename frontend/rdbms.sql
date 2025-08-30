-- =====================================================================
-- 📌 Ration Card Management System (RCMS)
-- =====================================================================
-- This SQL file creates the complete database schema, triggers, 
-- inserts demo data, and provides SELECT queries for testing.
-- Everything is self-documented so you can understand and run it
-- directly in MySQL Workbench.
-- 
-- Author: Your Name
-- =====================================================================

/***********************************************************************
 PART A — MAIN DATABASE: rcms1
 Used by Streamlit app (3.py) with full role-based system.
***********************************************************************/

-- 1) Drop & Create Database
DROP DATABASE IF EXISTS rcms1;
CREATE DATABASE rcms1 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE rcms1;

-- =========================================================
-- 2) USERS TABLE
-- Stores login credentials and roles for authentication.
-- Roles: Admin, Shopkeeper, Customer
-- =========================================================
CREATE TABLE USERS (
  username  VARCHAR(50) PRIMARY KEY,
  password  VARCHAR(255) NOT NULL,
  role      ENUM('Admin','Shopkeeper','Customer') NOT NULL
);

-- Insert demo users
INSERT INTO USERS VALUES
('admin','admin123','Admin'),
('ravi','ravi123','Shopkeeper'),
('anita','anita123','Customer');

-- =========================================================
-- 3) ADMIN TABLE
-- Stores details of system admins.
-- =========================================================
CREATE TABLE ADMIN (
  Admin_id   VARCHAR(10) PRIMARY KEY,
  A_Fname    VARCHAR(50) NOT NULL,
  A_Lname    VARCHAR(50) NOT NULL,
  A_Email_id VARCHAR(100),
  DOB        DATE,
  Age        INT CHECK (Age >= 18),
  Street_no  VARCHAR(20),
  PIN        VARCHAR(10)
);

INSERT INTO ADMIN VALUES
('A1','Super','Admin','admin@example.com','1990-01-01',35,'12','560001');

-- =========================================================
-- 4) SHOPKEEPER TABLE
-- Shopkeepers managed by Admins.
-- Linked to ADMIN table.
-- =========================================================
CREATE TABLE SHOPKEEPER (
  Shopkeeper_id VARCHAR(10) PRIMARY KEY,
  S_Fname       VARCHAR(50) NOT NULL,
  S_Lname       VARCHAR(50) NOT NULL,
  Store_name    VARCHAR(100),
  Street_no     VARCHAR(20),
  City          VARCHAR(50),
  PIN           VARCHAR(10),
  Admin_id      VARCHAR(10),
  FOREIGN KEY (Admin_id) REFERENCES ADMIN(Admin_id)
    ON UPDATE CASCADE ON DELETE SET NULL
);

INSERT INTO SHOPKEEPER VALUES
('S1','Ravi','K','Ravi Stores','221B','Bengaluru','560001','A1'),
('S2','Meena','P','Meena Mart','44','Mysuru','570001','A1');

-- =========================================================
-- 5) CUSTOMER TABLE
-- Stores customers linked to shopkeepers.
-- =========================================================
CREATE TABLE CUSTOMER (
  RFID           BIGINT PRIMARY KEY,
  C_Fname        VARCHAR(50),
  C_Lname        VARCHAR(50),
  C_Email_id     VARCHAR(100),
  DOB            DATE,
  Gender         ENUM('Male','Female','Other'),
  City           VARCHAR(50),
  PIN            VARCHAR(10),
  Shopkeeper_id  VARCHAR(10),
  FOREIGN KEY (Shopkeeper_id) REFERENCES SHOPKEEPER(Shopkeeper_id)
    ON UPDATE CASCADE ON DELETE SET NULL
);

INSERT INTO CUSTOMER VALUES
(1001,'Anita','Sharma','anita@example.com','1995-05-10','Female','Bengaluru','560001','S1'),
(1002,'Rahul','Verma','rahul@example.com','1990-03-22','Male','Mysuru','570001','S2');

-- =========================================================
-- 6) DEPENDENT TABLE
-- Stores dependents of customers.
-- Trigger ensures age >= 10.
-- =========================================================
CREATE TABLE DEPENDENT (
  RFID      BIGINT,
  D_Name    VARCHAR(100),
  DOB       DATE,
  Gender    ENUM('Male','Female','Other'),
  Age       INT,
  Relation  VARCHAR(50),
  PRIMARY KEY (RFID, D_Name),
  FOREIGN KEY (RFID) REFERENCES CUSTOMER(RFID)
    ON UPDATE CASCADE ON DELETE CASCADE
);

-- Trigger: age validation
DROP TRIGGER IF EXISTS dependent_age;
DELIMITER $$
CREATE TRIGGER dependent_age
BEFORE INSERT ON DEPENDENT
FOR EACH ROW
BEGIN
  IF NEW.Age < 10 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Dependent must be at least 10 years old';
  END IF;
END$$
DELIMITER ;

INSERT INTO DEPENDENT VALUES
(1001,'Rohit','2010-06-01','Male',14,'Son'),
(1002,'Neha','2012-08-12','Female',13,'Daughter');

-- =========================================================
-- 7) CUSTOMER_PHONE TABLE
-- One customer can have multiple phone numbers.
-- =========================================================
CREATE TABLE CUSTOMER_PHONE (
  RFID     BIGINT,
  Phone_no BIGINT,
  PRIMARY KEY (RFID, Phone_no),
  FOREIGN KEY (RFID) REFERENCES CUSTOMER(RFID)
    ON UPDATE CASCADE ON DELETE CASCADE
);

INSERT INTO CUSTOMER_PHONE VALUES
(1001,9876543210),
(1002,9123456780);

-- =========================================================
-- 8) SHOPKEEPER_PHONE TABLE
-- =========================================================
CREATE TABLE SHOPKEEPER_PHONE (
  Shopkeeper_id VARCHAR(10),
  Phone_no BIGINT,
  PRIMARY KEY (Shopkeeper_id, Phone_no),
  FOREIGN KEY (Shopkeeper_id) REFERENCES SHOPKEEPER(Shopkeeper_id)
    ON UPDATE CASCADE ON DELETE CASCADE
);

INSERT INTO SHOPKEEPER_PHONE VALUES
('S1',9988776655),
('S2',8877665544);

-- =========================================================
-- 9) BILL TABLE
-- Stores all ration bills.
-- =========================================================
CREATE TABLE BILL (
  Bill_id         VARCHAR(10) PRIMARY KEY,
  Total_cost      DECIMAL(10,2),
  Issued_date     DATE,
  Last_valid_date DATE,
  Present_date    DATE,
  Validity        VARCHAR(20),
  Shopkeeper_id   VARCHAR(10),
  RFID            BIGINT,
  FOREIGN KEY (Shopkeeper_id) REFERENCES SHOPKEEPER(Shopkeeper_id),
  FOREIGN KEY (RFID) REFERENCES CUSTOMER(RFID)
);

INSERT INTO BILL VALUES
('B1',1250.00,'2025-08-01','2025-08-31',CURDATE(),'Valid','S1',1001),
('B2',890.50,'2025-07-10','2025-07-31','2025-07-25','Invalid','S2',1002);

-- =========================================================
--  🔎 TEST QUERIES
-- =========================================================
SELECT * FROM USERS;
SELECT * FROM ADMIN;
SELECT * FROM SHOPKEEPER;
SELECT * FROM CUSTOMER;
SELECT * FROM DEPENDENT;
SELECT * FROM CUSTOMER_PHONE;
SELECT * FROM SHOPKEEPER_PHONE;
SELECT * FROM BILL;

-- Join: Customers with Dependents
SELECT c.C_Fname, c.C_Lname, d.D_Name, d.Relation
FROM CUSTOMER c LEFT JOIN DEPENDENT d ON c.RFID = d.RFID;

-- Join: Bills with Customer + Shopkeeper
SELECT b.Bill_id, b.Total_cost, b.Validity, c.C_Fname, s.Store_name
FROM BILL b
JOIN CUSTOMER c ON b.RFID = c.RFID
JOIN SHOPKEEPER s ON b.Shopkeeper_id = s.Shopkeeper_id;

-- Aggregate: Total spend per customer
SELECT c.C_Fname, c.C_Lname, SUM(b.Total_cost) AS Total_Spent
FROM CUSTOMER c
JOIN BILL b ON c.RFID = b.RFID
GROUP BY c.RFID;

-- ***********************************************************************
-- END OF FILE
-- ***********************************************************************
