# Frontend & Backend Integration Plan

## Overview
Connect the FastAPI backend (port 8000) with the HTML/CSS frontend by replacing the embedded Streamlit iframe with direct JavaScript API calls. This document outlines the complete integration strategy.

---

## Current Architecture

### Backend (FastAPI - Port 8000)
- **Server**: `backend/server.py`
- **Configuration**: `backend/config.py`
- **API Endpoints**:
  - `GET /health` - Health check with model status
  - `POST /followup-questions` - Generate adaptive follow-up questions
  - `POST /analyze` - Analyze symptoms and provide medical guidance
  - `GET /` - Serve frontend (index.html)

### Frontend (HTML/CSS - Static Files)
- **Main Page**: `frontend/index.html` (landing page with chatbot, contact form, login)
- **Dashboard**: `frontend/dashboard.html` (user dashboard)
- **Features**: `frontend/features.html` (feature descriptions)
- **Styling**: `frontend/style.css` (shared styles)

### Current Issue
- Frontend embeds Streamlit app (port 8501) in an iframe
- No direct communication between frontend and FastAPI backend
- Frontend has client-side OTP verification but no integrated authentication
- Contact form is client-side only (no backend submission)

---

## Integration Goals

### Primary Goal
Replace the Streamlit iframe with direct JavaScript API calls to FastAPI endpoints for a seamless, integrated chatbot experience.

### Secondary Goals
1. Enable contact form submission to backend
2. Connect dashboard to display session/analysis history
3. Implement proper error handling and loading states
4. Ensure CORS compatibility between frontend and backend
5. Maintain responsive design and UX consistency

---

## Implementation Plan

### Step 1: Create JavaScript API Client
**File**: `frontend/api.js`

**Purpose**: Wrapper functions to communicate with FastAPI backend

**Functionality**:
- `initAPI(baseURL)` - Initialize API client with configurable base URL
- `checkHealth()` - GET `/health` endpoint
- `getFollowupQuestions(symptoms)` - POST `/followup-questions`
  - Input: `{ symptoms: string }`
  - Output: `{ questions: string[] }`
- `analyzeSymptoms(initialSymptoms, followupAnswers)` - POST `/analyze`
  - Input: `{ initial_symptoms: string, followup_answers: string[] }`
  - Output: Analysis response with severity, confidence, possible conditions, etc.
- `submitContact(name, email, message)` - POST `/contact` (new endpoint)
  - Input: `{ name: string, email: string, message: string }`
  - Output: `{ status: success|error, message: string }`

**Features**:
- CORS-aware fetch requests
- Error handling with meaningful messages
- Request/response logging for debugging
- Timeout handling
- Default base URL: `http://localhost:8000`

---

### Step 2: Update index.html (Main Landing Page)
**File**: `frontend/index.html`

**Changes**:
1. **Remove**: Streamlit iframe embedded in the page
   ```html
   <!-- REMOVE THIS -->
   <iframe src="http://localhost:8501" style="width: 100%; height: 600px;"></iframe>
   ```

2. **Add**: New chatbot section with the following structure:
   - Initial symptom input field (textarea)
   - "Get Questions" button to fetch follow-up questions
   - Dynamic container for follow-up questions (radio/checkbox inputs)
   - "Analyze" button to submit answers and get analysis
   - Results container to display analysis output
   - Loading spinners/states during API calls

3. **Add**: Script tag linking to `api.js`
   ```html
   <script src="api.js"></script>
   ```

4. **Update**: JavaScript event handlers to use API client instead of:
   - Client-side OTP verification
   - Static messaging

5. **Update**: Contact form to use `submitContact()` API function

**HTML Structure**:
```
Chatbot Section
├── Symptom Input Form
│   ├── Textarea for initial symptoms
│   └── "Get Adaptive Questions" Button
├── Questions Container (dynamically populated)
│   ├── Follow-up Question 1 (radio/checkbox)
│   ├── Follow-up Question 2
│   └── Follow-up Question 3
├── Analyze Button
└── Results Container
    ├── Severity Badge
    ├── Confidence Score
    ├── Possible Conditions
    ├── Explanation
    ├── Home Care Tips
    ├── When to See Doctor
    └── Disclaimer

Contact Form (Updated)
├── Name Input
├── Email Input
├── Message Textarea
└── Submit Button (calls submitContact API)
```

---

### Step 3: Add Backend `/contact` Endpoint
**File**: `backend/server.py`

**New Endpoint**:
```python
@app.post("/contact")
async def submit_contact(contactData: ContactForm) -> Dict[str, str]:
    """
    Handle contact form submissions from frontend.
    
    Input:
    {
        "name": "John Doe",
        "email": "john@example.com",
        "message": "I have a question..."
    }
    
    Output:
    {
        "status": "success",
        "message": "Thank you for contacting us!"
    }
    """
    # Log contact information
    # Currently logs to console; can be extended with database storage
    logger.info(f"Contact form submission: {contactData.name} ({contactData.email})")
    
    return {
        "status": "success",
        "message": "Thank you for contacting us! We'll get back to you soon."
    }
```

**Pydantic Model** (add to `backend/models.py`):
```python
class ContactForm(BaseModel):
    name: str
    email: str
    message: str
```

---

### Step 4: Update dashboard.html
**File**: `frontend/dashboard.html`

**Changes**:
1. Remove static welcome message
2. Add JavaScript to fetch session/health data via `/health` endpoint
3. Display:
   - Active sessions count
   - Last analysis results
   - Link back to chatbot for new analyses
4. Add logging of analytics/usage data

**Sections**:
```
Dashboard
├── Welcome Section (dynamic, shows user info if available)
├── Session Summary
│   ├── Active Sessions Count
│   ├── Last Analysis Time
│   └── Previous Conditions Analyzed
└── Quick Actions
    ├── Start New Analysis (link to chatbot)
    └── View API Status (health check)
```

---

### Step 5: Update style.css
**File**: `frontend/style.css`

**New Styles**:
1. **Chatbot Container**
   - Responsive layout (mobile-first)
   - Clear sections for symptom input, questions, results
   - Proper spacing and padding

2. **Form Elements**
   - Styled input fields and textarea
   - Button styles (normal, hover, active, disabled states)
   - Toggle/radio button styles for follow-up questions

3. **Loading States**
   - Spinner animation
   - Disabled button states during API calls
   - Loading text messages

4. **Results Display**
   - Severity badge styling (color-coded: mild, moderate, severe)
   - Card-based layout for conditions and tips
   - Readable typography for long text

5. **Error Messages**
   - Error alert styling
   - Clear messaging and retry options

6. **Responsive Design**
   - Mobile breakpoints (≤768px, ≤480px)
   - Touch-friendly button sizes
   - Proper text scaling

---

### Step 6: Update index.html JavaScript Logic
**File**: `frontend/index.html` (inline scripts + api.js)

**Flow Implementation**:
```
1. User enters initial symptoms → Click "Get Questions"
   ↓
2. Frontend calls API: getFollowupQuestions(symptoms)
   ↓
3. Display follow-up questions dynamically
   ↓
4. User selects/enters answers → Click "Analyze"
   ↓
5. Frontend calls API: analyzeSymptoms(symptoms, answers)
   ↓
6. Display analysis results (severity, conditions, tips, etc.)
   ↓
7. Show disclaimer and options to refine or start new analysis
```

**Key Functions to Implement**:
```javascript
async function getFollowupQuestions() {
    // Get symptom input value
    // Call API client: api.getFollowupQuestions()
    // Display questions dynamically
    // Handle loading and error states
}

async function analyzeSymptoms() {
    // Collect follow-up answers
    // Call API client: api.analyzeSymptoms()
    // Display results
    // Handle loading and error states
}

async function handleContactSubmit(event) {
    // Get form data
    // Call API client: api.submitContact()
    // Show success/error message
    // Clear form on success
}

async function initDashboard() {
    // Call api.checkHealth()
    // Update dashboard with status
}
```

**Error Handling**:
- Network errors (backend down)
- Validation errors (empty input)
- CORS errors
- Timeout handling (5-10 second timeout)
- User-friendly error messages

---

### Step 7: Update CORS Configuration
**File**: `backend/server.py`

**Current CORS Settings** (check `backend/config.py`):
```python
ALLOWED_ORIGINS = ["http://localhost:3000", "http://localhost:8000"]
```

**Ensure**:
- If frontend is served by FastAPI (port 8000), keep `http://localhost:8000`
- If frontend runs on separate dev server (port 3000), keep both OR add additional origins
- CORS is enabled: `ENABLE_CORS = True`

**Frontend Base URL Configuration**:
- In `frontend/api.js`, set:
  ```javascript
  const API_BASE_URL = 'http://localhost:8000';
  ```

---

### Step 8: Testing & Validation
**Before Starting**:
- Ensure Python venv is activated
- All dependencies installed from `requirements.txt`
- Environment variables configured in `.env` file
- OPENROUTER_API_KEY is set

**Starting the Backend**:
```bash
cd backend
python server.py
# Expected output: "Uvicorn running on http://127.0.0.1:8000"
```

**Opening the Frontend**:
```
Navigate to: http://localhost:8000
```

**Test Cases**:

#### Chatbot Integration
- [ ] Navigate to main page, see chatbot section (NOT Streamlit iframe)
- [ ] Enter symptom text → Click "Get Questions" → View follow-up questions
- [ ] Select answers → Click "Analyze" → View analysis results
- [ ] Results show: severity, confidence, possible conditions, home care tips
- [ ] No CORS errors in browser console
- [ ] No 404 errors in Network tab (all API calls return 200)
- [ ] Loading states visible during API calls
- [ ] Error handling works if backend is offline

#### Contact Form
- [ ] Fill contact form with name, email, message
- [ ] Submit form
- [ ] See success message
- [ ] Backend logs show contact info
- [ ] Form clears after successful submission

#### Dashboard
- [ ] Navigate to dashboard
- [ ] See session summary or health status
- [ ] Link to start new analysis works
- [ ] No JavaScript errors in console

#### Browser DevTools Verification
- [ ] Network tab shows POST requests to `/followup-questions` and `/analyze`
- [ ] Request payload structure matches backend expectations
- [ ] Response JSON displays analysis data
- [ ] No failed requests (all 2xx status codes)
- [ ] Console shows no CORS warnings

---

## Technical Details

### API Request/Response Examples

#### POST /followup-questions
**Request**:
```json
{
  "symptoms": "I have a persistent cough and chest pain"
}
```

**Response**:
```json
{
  "questions": [
    "How long have you had this cough?",
    "Is the chest pain constant or intermittent?",
    "Do you have difficulty breathing?"
  ]
}
```

#### POST /analyze
**Request**:
```json
{
  "initial_symptoms": "I have a persistent cough and chest pain",
  "followup_answers": [
    "For 2 weeks",
    "It comes and goes",
    "Yes, especially when breathing deeply"
  ]
}
```

**Response**:
```json
{
  "severity": "Moderate",
  "confidence": "78%",
  "possible_conditions": ["Bronchitis", "Pneumonia", "GERD"],
  "explanation": ["Persistent cough + chest pain..."],
  "home_care_tips": ["Rest", "Stay hydrated", "Use humidifier"],
  "when_to_see_doctor": ["If cough persists > 3 weeks", "If fever > 101°F"],
  "disclaimer": "This is not a medical diagnosis. Consult a healthcare professional."
}
```

#### POST /contact
**Request**:
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "message": "I have a question about the chatbot"
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Thank you for contacting us!"
}
```

---

## Files to Create/Modify

### Create
- `frontend/api.js` - JavaScript API client

### Modify
- `frontend/index.html` - Replace Streamlit iframe, add chatbot UI, update form handlers
- `frontend/dashboard.html` - Add session display, update styling
- `frontend/style.css` - Add chatbot and form styles
- `backend/server.py` - Add `/contact` endpoint, verify CORS
- `backend/models.py` - Add `ContactForm` Pydantic model

### No Changes Needed
- `backend/app.py` - Core chatbot logic remains unchanged
- `backend/chatbot.py` - Analysis logic remains unchanged
- `backend/adaptive_questions.py` - Question generation remains unchanged
- `backend/rag.py` - RAG system remains unchanged
- Medical knowledge files - Remain unchanged

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    USER BROWSER                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │         Frontend HTML/CSS/JavaScript            │  │
│  │  ┌──────────────┐  ┌──────────────────┐         │  │
│  │  │ Chatbot Form │  │ Contact Form     │         │  │
│  │  │ • Symptom    │  │ • Name           │         │  │
│  │  │ • Questions  │  │ • Email          │         │  │
│  │  │ • Analysis   │  │ • Message        │         │  │
│  │  └──────────────┘  └──────────────────┘         │  │
│  │         ↓                ↓                        │  │
│  │    api.getFollowup      submitContact()          │  │
│  │    api.analyzeSymptoms() ...                     │  │
│  └─────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                           ↓ (HTTP/Fetch)
                   ┌───────────────────┐
                   │  CORS Enabled     │
                   │  localhost:8000   │
                   └───────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                 FastAPI Backend                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │              server.py (FastAPI App)            │  │
│  │                                                 │  │
│  │  POST /followup-questions                       │  │
│  │  ├─→ adaptive_questions.py                      │  │
│  │  └─→ Returns: questions[]                       │  │
│  │                                                 │  │
│  │  POST /analyze                                  │  │
│  │  ├─→ chatbot.py                                 │  │
│  │  ├─→ rag.py (FAISS index)                       │  │
│  │  ├─→ llm.py (OpenRouter/LLM)                    │  │
│  │  └─→ Returns: analysis results                  │  │
│  │                                                 │  │
│  │  POST /contact                                  │  │
│  │  ├─→ logger.py (log submission)                 │  │
│  │  └─→ Returns: success/error                     │  │
│  │                                                 │  │
│  │  GET /health                                    │  │
│  │  └─→ Returns: status, models_loaded             │  │
│  └─────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## Integration Checklist

- [ ] Create `frontend/api.js` with API client functions
- [ ] Update `frontend/index.html` - remove iframe, add chatbot form
- [ ] Update `frontend/style.css` - add chatbot styling
- [ ] Add `POST /contact` endpoint to `backend/server.py`
- [ ] Add `ContactForm` model to `backend/models.py`
- [ ] Test symptom → questions → analysis flow
- [ ] Test contact form submission
- [ ] Test dashboard updates
- [ ] Verify CORS headers in browser Network tab
- [ ] Verify no console errors in browser DevTools
- [ ] Test error handling (backend offline scenario)
- [ ] Test on mobile responsive breakpoints
- [ ] Verify all API endpoints return expected responses

---

## Future Enhancements

1. **WebSocket Support**: Use `/ws/chat` endpoint for real-time streaming responses
2. **Authentication**: Implement JWT token-based user authentication
3. **Database**: Store contact submissions and analysis history in a database
4. **User Sessions**: Track user session history across browser sessions
5. **Analytics**: Track usage patterns and popular symptoms
6. **Caching**: Cache follow-up questions and analysis results
7. **Multi-language**: Support multiple languages for questions and responses
8. **Accessibility**: Improve WCAG accessibility compliance
9. **Performance**: Optimize bundle size, add service worker for offline support
10. **Mobile App**: Convert to mobile app using React Native or Flutter

---

## Troubleshooting

### CORS Error
**Problem**: "Access to XMLHttpRequest has been blocked by CORS policy"
**Solution**:
- Verify `ENABLE_CORS = True` in `config.py`
- Check `ALLOWED_ORIGINS` includes frontend URL
- Ensure backend is running on correct port
- Check browser DevTools → Network → Response Headers for `Access-Control-Allow-Origin`

### API Returns 404
**Problem**: "POST /analyze 404 Not Found"
**Solution**:
- Verify backend is running: `python backend/server.py`
- Check `api.js` base URL matches backend URL
- Verify endpoint names match exactly (case-sensitive)
- Check server logs for errors

### Symptoms Not Showing Questions
**Problem**: Form submitted but no questions appear
**Solution**:
- Open browser DevTools Console for error messages
- Check Network tab to see if API request was sent
- View response to see if questions array is populated
- Verify LLM API key is set in `.env`

### Contact Form Won't Submit
**Problem**: Submit button does nothing or shows error
**Solution**:
- Check browser console for JavaScript errors
- Verify `/contact` endpoint exists in backend
- Check request payload matches `ContactForm` model
- Review backend logs for submission errors

---

## Configuration

### Backend Environment Variables (.env)
```
OPENROUTER_API_KEY=your_api_key_here
HOST=127.0.0.1
PORT=8000
DEBUG=False
ENABLE_CORS=True
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

### Frontend Configuration (hardcoded in api.js)
```javascript
const API_BASE_URL = 'http://localhost:8000';
const API_TIMEOUT = 10000; // 10 seconds
```

---

## Performance Considerations

- **API Response Time**: Average 2-5 seconds for analysis (LLM processing)
- **FAISS Index Load**: ~500ms on first request
- **Frontend Bundle Size**: Minimal (no external dependencies except for styling)
- **Network Bandwidth**: 1-5 KB per request, 5-20 KB per response

---

## Security Notes

1. **API Keys**: Never expose `OPENROUTER_API_KEY` in frontend code
2. **CORS**: Only allow trusted origins
3. **Input Validation**: Backend validates all requests via Pydantic
4. **Rate Limiting**: 60 requests/min per IP (configurable)
5. **HTTPS**: Deploy with HTTPS in production (currently HTTP for local dev)
6. **User Data**: Currently no persistent storage; consider privacy implications before adding database

---

## Contact & Support

For integration questions or issues, refer to:
- Backend logs: `python server.py` console output
- Browser DevTools: F12 → Console & Network tabs
- API Documentation: `http://localhost:8000/api-docs` (Swagger UI)

---

**Last Updated**: March 1, 2026  
**Status**: Ready for Implementation
