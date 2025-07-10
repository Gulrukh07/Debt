
# 💰 Debt Management App

A simple and efficient Django-based web application for tracking personal debts and payments.

## 📌 Features

- ✅ Add, update, and delete **debts**
- ✅ Record **payments** and link them to specific debts
- ✅ View a combined activity feed of debts and payments
- ✅ Organize entries by **contacts** and **categories**
- ✅ Secure user **authentication** and session management
- ✅ Clean and responsive user interface using Django templates
- ✅ Uses Django Class-Based Views (CBVs) for clean architecture

## 🛠️ Technologies Used

- Python 3
- Django 4+
- SQLite (default) – easy to replace with PostgreSQL
- HTML/CSS (Django templates)
- Bootstrap (for UI styling)
- Python's `itertools` and `operator` modules for efficient sorting and merging

## 🚀 Setup Instructions

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Gulrukh07/Debt.git
   cd Debt


2. **Create and activate a virtual environment**:

   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**:

   ```bash
   python manage.py migrate
   ```

5. **Create a superuser**:

   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server**:

   ```bash
   python manage.py runserver
   ```


## 📂 App Structure

* `debt/` – Main app containing models, views, and forms
* `templates/` – All HTML templates used for rendering pages
* `static/` – Static files (CSS, JS, etc.)
* `users/` – Custom user-related logic and authentication

## 🧠 How It Works

* Debts and Payments are two separate models but are combined in the view using `itertools.chain` and sorted by `created_at`.
* Each user can manage their own debt records and filter by contact or category.
* Simple and intuitive layout makes it easy to track financial activities.


## 🙋‍♀️ Author

Built with 💙 by [Gulrukh Khayrullaeva](https://github.com/Gulrukh07)

