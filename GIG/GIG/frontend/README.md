# Healthcare Assistant - Frontend

Simple, clean frontend for the Healthcare Multi-Agent System.

## 🚀 Quick Start

### 1. Start the Backend
```bash
# From GIG directory
uvicorn app.main:app --reload
```
Backend runs at: `http://localhost:8000`

### 2. Open the Frontend
Simply open `index.html` in your browser:

**Option 1: Double-click**
- Navigate to `frontend/` folder
- Double-click `index.html`

**Option 2: Python Server**
```bash
cd frontend
python -m http.server 8080
```
Then open: `http://localhost:8080`

**Option 3: VS Code Live Server**
- Right-click `index.html`
- Select "Open with Live Server"

## 📱 Features

### 🔐 Authentication
- **Sign Up**: Create a new account
- **Login**: Access your documents and chat

### 💬 Chat Interface
- Ask questions to the AI assistant
- Get responses with citations
- **Quick Actions** for common queries:
  - 🩺 Explain Diagnosis
  - 💰 Check Bill
  - 💊 Medicine Prices
  - 🍎 Diet Plan

### 📄 Document Management
- View all uploaded documents
- See processing status
- Document type badges (Discharge/Bill)

### ⬆️ Document Upload
- Upload **Discharge Summaries** (PDF)
- Upload **Hospital Bills** (PDF)
- Background processing (30-60 seconds)

## 🎨 Design

Clean, simple design with:
- Purple gradient theme
- Responsive layout
- Emoji icons (no external dependencies)
- Smooth animations

## 🔧 Configuration

If your backend runs on a different port, edit `app.js`:
```javascript
const API_BASE = 'http://localhost:8000';  // Change port here
```

## 📊 Usage Flow

### First Time User
1. **Sign Up** with email and password
2. **Login** with credentials
3. **Upload Documents**:
   - Go to "Upload" tab
   - Choose PDF file
   - Click "Upload"
   - Wait 30-60 seconds for processing
4. **Start Chatting**:
   - Go to "Chat" tab
   - Type question or use Quick Actions
   - Get AI-powered responses

### Example Questions
```
"Explain my diagnosis in simple terms"
"Check my hospital bill for overcharging"
"Compare prices for paracetamol 500mg"
"Create a 7-day meal plan for my condition"
"What medications was I prescribed?"
```

## 🗂️ File Structure
```
frontend/
├── index.html    # Main HTML structure
├── style.css     # All styling
├── app.js        # JavaScript logic
└── README.md     # This file
```

## 🎯 Key Features

### Multi-Agent Responses
When you ask complex questions like:
> "Explain my diagnosis and check my bill"

The system automatically:
1. Routes to both agents (Discharge + Bill)
2. Runs them in parallel
3. Aggregates results
4. Shows combined response

### Citations
All responses include citations like:
```
According to [1], you were diagnosed with...

Sources:
[1] discharge_summ_pdf_2.pdf - Page 3
```

### Real-Time Updates
- Documents show processing status
- Chat updates instantly
- Upload progress indicators

## 🔍 Troubleshooting

### "Connection error"
- Check if backend is running: `http://localhost:8000`
- Look for CORS errors in browser console
- Verify API_BASE in `app.js` matches backend port

### "Login failed"
- Make sure backend database is initialized
- Check credentials
- Look at backend terminal for errors

### "Upload failed"
- Check file is PDF format
- File size should be < 10MB (adjustable in backend)
- Ensure you're logged in

### Documents show "Processing..."
- Normal! Background processing takes 30-60 seconds
- Refresh documents list after 1 minute
- Check backend terminal for processing logs

## 💡 Tips

1. **Quick Actions**: Use sidebar buttons for common queries
2. **Multiple Documents**: Upload multiple files, system handles them all
3. **Chat History**: Stays until you refresh (no persistence yet)
4. **Logout**: Clears all local data

## 🎨 Customization

### Change Theme Colors
Edit `style.css`:
```css
/* Main gradient */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* Primary color */
.btn-primary {
    background: #667eea;  /* Change this */
}
```

### Add More Quick Actions
Edit `index.html`:
```html
<button class="quick-btn" onclick="askQuestion('Your question here')">
    🎯 Your Label
</button>
```

## 📈 Future Enhancements (Optional)

- [ ] Chat history persistence
- [ ] Document preview
- [ ] Export chat as PDF
- [ ] Voice input
- [ ] Dark mode toggle
- [ ] Mobile app wrapper

## ✅ Ready to Use!

1. Backend running? ✓
2. Frontend open? ✓
3. Account created? ✓
4. Documents uploaded? ✓
5. Start chatting! 🎉

---

**Built with**: Vanilla JavaScript, HTML5, CSS3  
**Dependencies**: None (uses browser APIs only)  
**Works with**: Chrome, Firefox, Safari, Edge (modern versions)
