# 🧪 Testing & Verification Guide

## **Quick Start Testing**

### **Prerequisites**
1. MongoDB running and accessible
2. Backend dependencies installed (`pip install -r requirements.txt`)
3. Frontend dependencies installed (`npm install` in both frontend directories)

---

## **Step 1: Start Backend**

```bash
cd c:\Users\sudanva\Desktop\start\backend
python start_server.py
```

**Expected Output:**
```
============================================================
Starting Astrology Backend Server...
============================================================
Backend Directory: ...
Calculation Source: ...
============================================================
INFO:     Started server process [XXXX]
INFO:     Waiting for application startup.
INFO:     Loading environment variables...
INFO:     Connecting to MongoDB...
INFO:     Preloading world city index...
INFO:     World city index loaded successfully.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080
```

**Verify:**
- ✅ No errors during startup
- ✅ MongoDB connected successfully
- ✅ World city index loaded
- ✅ Server running on port 8080

---

## **Step 2: Start Frontend**

```bash
cd c:\Users\sudanva\Desktop\start\frontend
npm run dev
```

**Expected Output:**
```
VITE v5.x.x ready in XXX ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

**Verify:**
- ✅ Vite server running on port 5173 (or configured port)
- ✅ No build errors

---

## **Step 3: Test Main Website**

### **3.1 Homepage**
1. Open browser: `http://localhost:5173/`
2. **Verify:**
   - ✅ Page loads without errors
   - ✅ Navbar appears with "Astro Care" logo
   - ✅ "Login" button visible (if not logged in)
   - ✅ Navigation links visible (Home, Horoscope, Birth Chart, etc.)

### **3.2 Login/Signup**
1. Click "Login" button
2. **Verify:**
   - ✅ Redirected to `/auth` page
   - ✅ Sign Up / Login toggle works
   - ✅ Google OAuth button visible

3. **Test Signup:**
   - Enter: Name, Email, Password
   - Click "Create Account"
   - **Expected:** Success toast + auto-login

4. **Test Login:**
   - Enter: Email, Password
   - Click "Sign In"
   - **Expected:** Success toast + redirect to home

5. **Verify After Login:**
   - ✅ Navbar shows profile icon (with your initial)
   - ✅ Click profile icon → dropdown menu appears
   - ✅ Dropdown shows: My Profile, Birth Chart, Logout

---

## **Step 4: Test Horoscope Integration**

### **4.1 Navigate to Horoscope**
1. Click "Horoscope" in navbar
2. **Expected:**
   - Loading spinner appears briefly
   - Redirects to `http://localhost:8080/horoscope/`

3. **Verify Horoscope Page:**
   - ✅ Page loads without errors
   - ✅ **NEW NAVBAR appears** at top
   - ✅ Navbar shows:
     - Back button (← Back)
     - Astro Care logo
     - "Horoscope Dashboard" text
     - Profile icon (if logged in) OR Login button (if not logged in)

### **4.2 Test Back Button**
1. Click "← Back" button in navbar
2. **Expected:**
   - Returns to previous page (main website)
   - Browser history works correctly

### **4.3 Test Navbar Logo Link**
1. Click "Astro Care" logo in horoscope navbar
2. **Expected:**
   - Redirects to main website homepage

---

## **Step 5: Test Horoscope Calculation (Logged In)**

### **5.1 Generate Horoscope**
1. Make sure you're logged in (check profile icon in navbar)
2. Fill in horoscope form:
   - **Birth DateTime:** 2000-01-01 06:30
   - **Place:** Chennai (search and select from dropdown)
   - **TZ Offset:** Auto-filled
   - Leave other fields as default
3. Click "Generate Horoscope" or equivalent submit button

### **5.2 Verify Auto-Save**
1. Open browser console (F12 → Console tab)
2. Look for log message:
   ```
   Horoscope saved to database for user: your-email@example.com
   ```
3. **Expected:**
   - ✅ No errors in console
   - ✅ "Horoscope saved" message appears

### **5.3 Verify MongoDB Storage**
1. **Check MongoDB directly** (optional):
   ```javascript
   // In MongoDB Compass or shell:
   db.horoscopes.find({ user_email: "your-email@example.com" })
   db.horoscope_chunks.find({ user_email: "your-email@example.com" })
   ```

2. **Expected:**
   - ✅ One document in `horoscopes` collection
   - ✅ Multiple documents in `horoscope_chunks` collection
   - ✅ Documents contain compressed horoscope data

---

## **Step 6: Test Horoscope Calculation (Anonymous)**

### **6.1 Logout**
1. Click profile icon in navbar
2. Click "Logout"
3. **Verify:**
   - ✅ Redirected to homepage
   - ✅ Navbar shows "Login" button instead of profile

### **6.2 Navigate to Horoscope (Anonymous)**
1. Click "Horoscope" in navbar
2. **Verify:**
   - ✅ Horoscope page loads
   - ✅ Navbar shows "Login" button (not profile icon)

### **6.3 Generate Horoscope (Anonymous)**
1. Fill in horoscope form (same as before)
2. Click submit
3. **Verify:**
   - ✅ Horoscope generates successfully
   - ✅ All charts and data display correctly
   - ✅ **NO auto-save message in console**
   - ✅ No errors

### **6.4 Verify NO Storage**
1. Check browser console
2. **Expected:**
   - ✅ No "Horoscope saved" message
   - ✅ No storage-related errors
   - ✅ Calculation works normally

---

## **Step 7: Test Profile Page**

### **7.1 Navigate to Profile**
1. Login if not already logged in
2. Click profile icon → "My Profile"
3. **Verify:**
   - ✅ Profile page loads
   - ✅ User information displayed
   - ✅ Tabs work (Overview, My Charts, Readings, Settings)

### **7.2 Test Logout from Profile**
1. Scroll down and click "Logout" button
2. **Verify:**
   - ✅ Redirected to homepage
   - ✅ Session cleared
   - ✅ Navbar shows "Login" button

---

## **Step 8: Test Cross-Site Auth Sync**

### **8.1 Login on Main Site**
1. Open main site: `http://localhost:5173/`
2. Login via `/auth` page
3. Note: You should see profile icon in navbar

### **8.2 Check Auth on Horoscope Site**
1. Navigate to horoscope: `http://localhost:8080/horoscope/`
2. **Expected:**
   - ✅ Horoscope navbar shows profile icon
   - ✅ User email displayed in profile dropdown
   - ✅ "✓ Data will be saved" indicator visible

### **8.3 Logout from Horoscope Site**
1. Click profile icon in horoscope navbar
2. Click "Logout"
3. **Expected:**
   - ✅ Redirects to main site homepage
   - ✅ Session cleared everywhere
   - ✅ Main site navbar also shows "Login" button

---

## **Step 9: Test Error Handling**

### **9.1 Test Invalid Horoscope Input**
1. Try submitting horoscope form with:
   - Empty date
   - Invalid timezone offset (e.g., 20)
   - Invalid coordinates
2. **Expected:**
   - ✅ Form validation errors display
   - ✅ Submit button disabled or errors shown
   - ✅ No API calls made

### **9.2 Test Backend Connection Failure**
1. Stop backend server
2. Try to generate horoscope
3. **Expected:**
   - ✅ Graceful error message (not raw error)
   - ✅ User informed of connection issue

---

## **Step 10: Test Browser Navigation**

### **10.1 Forward/Back Navigation**
1. Navigate: Home → Horoscope → Back (browser button) → Forward (browser button)
2. **Expected:**
   - ✅ All navigations work smoothly
   - ✅ No infinite loops
   - ✅ No broken states

### **10.2 Refresh Page**
1. While on horoscope page (logged in):
2. Press F5 to refresh
3. **Expected:**
   - ✅ Page reloads successfully
   - ✅ Auth state preserved (profile icon still visible)
   - ✅ Previous form data may be lost (expected)

---

## **🐛 Common Issues & Solutions**

### **Issue: "Database not initialized" error**
**Cause:** MongoDB connection failed  
**Solution:**
1. Check MongoDB is running
2. Verify `MONGO_URI` in `backend/.env`
3. Restart backend server

### **Issue: Horoscope page shows 404**
**Cause:** Horoscope frontend not built  
**Solution:**
```bash
cd backend/calculation/calculation-main/frontend
npm run build
```

### **Issue: CORS errors in console**
**Cause:** Backend CORS config mismatch  
**Solution:**
- Check `backend/main.py` CORS settings allow frontend origin

### **Issue: "Failed to auto-save horoscope"**
**Cause:** Auth token expired or invalid  
**Solution:**
1. Logout and login again
2. Check token in localStorage
3. Verify backend auth endpoint is working

### **Issue: Navbar not showing on horoscope page**
**Cause:** Old build cached  
**Solution:**
```bash
cd backend/calculation/calculation-main/frontend
npm run build
# Restart backend server
```

---

## **✅ Success Criteria**

All tests should pass:

### **Authentication**
- [x] Signup creates new user
- [x] Login works with email/password
- [x] Google OAuth login works
- [x] Logout clears session
- [x] Token persists on refresh
- [x] Auth state syncs between main site and horoscope

### **Horoscope Functionality**
- [x] Horoscope page loads with navbar
- [x] Back button returns to main site
- [x] Horoscope calculation works for logged-in users
- [x] Horoscope calculation works for anonymous users
- [x] Auto-save happens ONLY for logged-in users
- [x] No errors for anonymous users

### **Navigation**
- [x] All navbar links work
- [x] Browser back/forward buttons work
- [x] Page refresh preserves auth state
- [x] No infinite loading loops

### **Storage**
- [x] Logged-in user's horoscope is stored in MongoDB
- [x] Anonymous user's horoscope is NOT stored
- [x] Compression pipeline works correctly
- [x] Dasha data is included in storage

---

## **📊 Final Verification Checklist**

Before deploying to production:

- [ ] All tests above pass
- [ ] No console errors
- [ ] No network errors
- [ ] MongoDB connections stable
- [ ] Auth tokens working correctly
- [ ] Compression reduces data size significantly
- [ ] Horoscope results are accurate
- [ ] UI is responsive on mobile
- [ ] All environment variables configured correctly
- [ ] Production secrets are different from dev

---

## **🚀 Ready for Production**

Once all tests pass, the system is ready for deployment. Remember to:

1. Update environment variables for production
2. Use production MongoDB URI
3. Configure proper CORS origins
4. Enable HTTPS
5. Set secure cookie flags
6. Add rate limiting
7. Add monitoring and logging

---

**Happy Testing! 🎉**
