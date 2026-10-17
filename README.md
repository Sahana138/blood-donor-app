# Emergency Blood Donor Alert System

When someone needs blood urgently, this app finds compatible, eligible donors nearby and alerts them. A donor accepts with one click, and only then does the requester see the donor's phone number.

## Why this project
Existing tools such as e-RaktKosh and Friends2Support mostly give a search-and-call list. This app pushes the request to the nearest eligible donors, handles accept/decline, and widens the search automatically if nobody responds.

## Features
- JWT registration and login. One account can both request blood and donate (tabs: "I need blood" / "I can donate").
- Matching by blood-group compatibility, availability, a 90-day donation gap, and distance (Haversine), nearest first.
- Donors are alerted in waves: the 5 nearest within 10 km, then 20 km, then 30 km if nobody accepts.
- In-app donor inbox with Accept / Decline, refreshed every 5 seconds. Email links work too.
- First acceptance wins: the request is closed with a single atomic database update, so two donors can never both win.
- The donor's phone number is shared only after acceptance. Declined donors are not alerted again for that request.
- A requester is never alerted about their own request.
- Live request page with an OpenStreetMap (Leaflet) map: hospital, alerted donors (approximate locations only), and the accepted donor in green.

## Tech stack
| Layer | Technology |
|---|---|
| Frontend | React (Vite), React Router, Leaflet / OpenStreetMap, served by nginx |
| Backend | FastAPI, SQLAlchemy, Pydantic |
| Database | MySQL 8 (SQLite for quick local runs) |
| Auth | JWT, bcrypt password hashing |
| DevOps | Docker, Docker Compose, Jenkins, pytest |

## Architecture
```
React (nginx :5173)  ->  FastAPI (:8000)  ->  MySQL
                              |
                              +-> email alerts (printed to logs unless SMTP is set)
```

CI/CD pipeline (`Jenkinsfile`), triggered by polling GitHub every 5 minutes:
1. Build backend image
2. Run the pytest suite inside the image
3. Build frontend image
4. Deploy with `docker compose up -d --build`
5. Smoke test: check the backend answers

## How a request works
1. A requester enters the blood group, hospital and location.
2. The backend finds compatible, available donors who have not donated in the last 90 days, and alerts the 5 nearest.
3. Each donor sees the request in their inbox (and in the email) and accepts or declines.
4. The first acceptance closes the request. The requester sees the donor's name and phone, and the map dot turns green.
5. If nobody accepts, a background task alerts the next donors after a wait (10 minutes by default), with a wider radius.

## Run it
Requires Docker Desktop.

```
git clone https://github.com/Sahana138/blood-donor-app.git
cd blood-donor-app
docker compose up --build
docker compose exec backend python seed.py
```

Open http://localhost:5173. API docs are at http://localhost:8000/docs.

If the backend is not running after the first start (it can start before MySQL is ready), run `docker compose up -d backend`.

Optional settings go in `backend/.env`: `SECRET_KEY`, `BASE_URL`, `WAVE_MINUTES`, `SMTP_USER`, `SMTP_PASSWORD`. Without SMTP settings, alert emails are printed in the backend logs.

### Run without Docker
```
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```
```
cd frontend
npm install
npm run dev
```
The backend uses SQLite when `DATABASE_URL` is not set.

## Try the demo
1. Register three users (for example Ravi, Anil, Meera) and open each in a separate browser window (a login is kept per tab).
2. Anil and Meera: open "I can donate", set blood group B+ and a location, then save.
3. Ravi: open "I need blood", choose B+, enter a hospital and send the request.
4. Anil's and Meera's inboxes show the request. Anil accepts.
5. Ravi's page shows Anil's name and phone, and Meera sees "Another donor has already accepted".

## Tests
```
cd backend
pytest -v
```
9 tests cover blood-group compatibility, distance calculation, registration, login, and protected routes.

## API overview
| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/auth/register`, `/auth/login` | Create an account, get a JWT |
| GET | `/auth/me` | Current user |
| PUT / GET | `/donors/me` | Save / read donor profile |
| POST | `/requests` | Create a blood request and alert donors |
| GET | `/requests/{id}` | Request status, map data, accepted donor |
| GET | `/alerts/mine` | Donor inbox |
| POST | `/alerts/{id}/respond` | Accept or decline from the app |
| GET | `/alerts/respond` | Accept or decline from an email link |

## Screenshots
E:\saana\Projects\blood-donor-app\screenshots
[Request page with map and accepted donor]
[Donor inbox]
[Jenkins stage view]

## Limitations and future work
- Pending alert waves are held in memory and are lost if the server restarts. A job queue such as Celery would fix this.
- Location is typed or filled with the browser's location button. A place search and a map picker would help in an emergency.
- Phone numbers are not verified with OTP yet.
- Demo donors are synthetic data created by `seed.py`.
- Passwords and keys in `docker-compose.yml` and the default `SECRET_KEY` are for local demos only. Use secrets management in production.
- Jenkins runs in Docker with the Docker socket mounted. This is fine for a local demo but not for production.