# Running BookingSoft (React SPA + Django API)

BookingSoft uses a decoupled architecture with a React.js (Vite) frontend and a Django REST API backend. 

You need to run three processes simultaneously:

## 1. The Django Backend API
This serves all data via JSON endpoints and handles business logic.

```powershell
# Open Terminal 1
.\.venv\Scripts\Activate.ps1
cd backend
python manage.py runserver
```

The API base URL is `http://127.0.0.1:8000/api/v1/`.

## 2. The Background Task Worker
This handles asynchronous tasks like confirming emails and expiring unpaid cash holds.

```powershell
# Open Terminal 2
.\.venv\Scripts\Activate.ps1
cd backend
python manage.py qcluster
```

## 3. The React Frontend
This is the user interface. It runs on a Node.js development server (Vite).

```powershell
# Open Terminal 3
cd frontend
npm run dev
```

The application UI will be available in your browser at `http://localhost:5173/`.

---

## Initial Setup (If starting from scratch)
If this is your first time cloning the project, ensure you run the migrations, create a superuser, and install Node dependencies:

**Backend Setup:**
```powershell
.\.venv\Scripts\Activate.ps1
cd backend
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

**Frontend Setup:**
```powershell
cd frontend
npm install
```
