"""
Creates a sample SQLite database (company.db) with 5 related tables:
departments, employees, projects, assignments, clients.
"""

import sqlite3

conn = sqlite3.connect("company.db")
c = conn.cursor()

c.executescript("""
CREATE TABLE departments (
    dept_id INTEGER PRIMARY KEY,
    dept_name TEXT NOT NULL
);

CREATE TABLE employees (
    emp_id INTEGER PRIMARY KEY,
    emp_name TEXT NOT NULL,
    salary INTEGER,
    dept_id INTEGER,
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
);

CREATE TABLE projects (
    project_id INTEGER PRIMARY KEY,
    project_name TEXT NOT NULL,
    dept_id INTEGER,
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
);

CREATE TABLE assignments (
    assignment_id INTEGER PRIMARY KEY,
    emp_id INTEGER,
    project_id INTEGER,
    hours_worked INTEGER,
    FOREIGN KEY (emp_id) REFERENCES employees(emp_id),
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);

CREATE TABLE clients (
    client_id INTEGER PRIMARY KEY,
    client_name TEXT NOT NULL,
    project_id INTEGER,
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);

INSERT INTO departments VALUES (1,'Engineering'),(2,'Sales'),(3,'HR');

INSERT INTO employees VALUES
(1,'Amit Sharma',75000,1),
(2,'Priya Singh',82000,1),
(3,'Rahul Verma',60000,2),
(4,'Sneha Patil',55000,3),
(5,'Vikram Rao',90000,1);

INSERT INTO projects VALUES
(1,'Website Revamp',1),
(2,'Sales CRM',2),
(3,'Payroll System',3);

INSERT INTO assignments VALUES
(1,1,1,120),
(2,2,1,150),
(3,5,3,80),
(4,3,2,100);

INSERT INTO clients VALUES
(1,'Tata Motors',1),
(2,'Infosys',2);
""")

conn.commit()
conn.close()
print("company.db created with 5 tables")